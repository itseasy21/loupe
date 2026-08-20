from __future__ import annotations

import sys
from types import ModuleType, SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from loupe import __version__
from loupe.api.server import create_app
from loupe.causal.attributor import rank_failed_spans
from loupe.causal.graph import build_causal_graph
from loupe.core.trace import Span, SpanKind, SpanStatus, Trace
from loupe.eval.evaluator import DeterministicEvaluator
from loupe.eval.judge import DeterministicJudge, JudgeResult
from loupe.integrations.langchain import LoupeCallbackHandler
from loupe.replay.engine import ReplayEngine
from loupe.storage.arrow import ParquetTraceStore
from loupe.storage.sqlite import SQLiteTraceStore


def test_causal_graph_and_blame_scores() -> None:
    trace = Trace(name="failed-agent")
    root = trace.add_span(Span(name="agent", kind=SpanKind.AGENT))
    child = trace.add_span(Span(name="tool", kind=SpanKind.TOOL, parent_id=root.span_id))
    child.finish(SpanStatus.ERROR, "boom")

    graph = build_causal_graph(trace)
    scores = rank_failed_spans(trace)

    assert graph.nodes[root.span_id].name == "agent"
    assert graph.parents_of(child.span_id) == {root.span_id}
    assert scores[0].span_id == child.span_id


def test_deterministic_judge_scores_errors() -> None:
    empty_result = DeterministicJudge().judge(Trace(name="empty"))
    trace = Trace(name="mixed")
    trace.add_span(Span(name="ok", kind=SpanKind.LLM, status=SpanStatus.OK))
    trace.add_span(Span(name="bad", kind=SpanKind.TOOL, status=SpanStatus.ERROR))

    result = DeterministicJudge().judge(trace)

    assert empty_result.dimension == "overall"
    assert not empty_result.passed
    assert not result.passed
    assert result.score == 0.5
    assert result.reason == "error spans found"


def test_deterministic_judge_keeps_requested_dimension() -> None:
    result = DeterministicJudge("safety").judge(Trace(name="empty"))

    assert result.dimension == "safety"
    assert result.reason == "trace has no spans"


def test_deterministic_evaluator_scores_errors() -> None:
    empty_result = DeterministicEvaluator().evaluate(Trace(name="empty"))
    trace = Trace(name="mixed")
    trace.add_span(Span(name="ok", kind=SpanKind.LLM, status=SpanStatus.OK))
    trace.add_span(Span(name="bad", kind=SpanKind.TOOL, status=SpanStatus.ERROR))

    result = DeterministicEvaluator().evaluate(trace)

    assert not empty_result.passed
    assert empty_result.score == 0.0
    assert empty_result.reason == "failed dimensions: correctness, safety, format"
    assert set(empty_result.dimensions) == {"correctness", "safety", "format"}
    assert not result.passed
    assert result.score == 0.5
    assert result.reason == "failed dimensions: correctness, safety, format"
    assert result.dimensions["correctness"].score == 0.5


def test_deterministic_evaluator_accepts_custom_judges() -> None:
    class FakeJudge:
        def __init__(self, dimension: str, passed: bool, score: float) -> None:
            self.dimension = dimension
            self.passed = passed
            self.score = score

        def judge(self, trace: Trace) -> JudgeResult:
            return JudgeResult(self.dimension, self.passed, self.score, f"judged {trace.name}")

    result = DeterministicEvaluator(
        judges=[
            FakeJudge("correctness", True, 1.0),
            FakeJudge("safety", False, 0.25),
            FakeJudge("format", True, 0.5),
        ]
    ).evaluate(Trace(name="support-agent"))

    assert not result.passed
    assert result.score == 0.5833333333333334
    assert result.reason == "failed dimensions: safety"
    assert result.dimensions["safety"].passed is False
    assert result.dimensions["format"].score == 0.5


def test_replay_engine_uses_stored_tool_outputs(monkeypatch: pytest.MonkeyPatch) -> None:
    module = ModuleType("fake_tool_module")

    def lookup() -> str:
        return "live"

    module.lookup = lookup  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "fake_tool_module", module)
    trace = Trace(name="replay")
    trace.add_span(
        Span(
            name="lookup",
            kind=SpanKind.TOOL,
            attributes={"patch_target": "fake_tool_module.lookup"},
            outputs={"return_value": "recorded"},
        )
    )

    def run_agent() -> str:
        import fake_tool_module

        return fake_tool_module.lookup()

    result = ReplayEngine().replay(trace, run_agent)

    assert result.returned == "recorded"
    assert result.mocked_calls == 1


def test_langchain_callback_handler_records_lifecycle() -> None:
    handler = LoupeCallbackHandler()

    handler.on_chain_start({"name": "chain"}, {"input": "hello"}, "run-1")
    handler.on_chain_end({"output": "world"}, "run-1")
    handler.on_chain_start({}, {}, "run-2")
    handler.on_chain_error(RuntimeError("bad"), "run-2")

    assert handler.trace.spans[0].outputs == {"output": "world"}
    assert handler.trace.spans[1].status == SpanStatus.ERROR


def test_api_lists_loads_and_analyzes_traces(tmp_path) -> None:  # type: ignore[no-untyped-def]
    database = tmp_path / "api.db"
    store = SQLiteTraceStore(database)

    first = Trace(name="api-agent")
    first_root = first.add_span(Span(name="agent.run", kind=SpanKind.AGENT, status=SpanStatus.OK))
    first.add_span(
        Span(
            name="tool.lookup",
            kind=SpanKind.TOOL,
            parent_id=first_root.span_id,
            status=SpanStatus.OK,
        )
    )
    first.finish()
    store.save_trace(first)

    second = Trace(name="searchable-agent")
    second_root = second.add_span(Span(name="agent.run", kind=SpanKind.AGENT, status=SpanStatus.OK))
    second.add_span(
        Span(
            name="tool.lookup",
            kind=SpanKind.TOOL,
            parent_id=second_root.span_id,
            status=SpanStatus.ERROR,
            inputs={"query": "refund policy"},
            error="lookup failed",
        )
    )
    second.finish()
    store.save_trace(second)
    app = create_app(database)
    client = TestClient(app)

    assert app.version == __version__
    assert client.get("/health").json() == {"status": "ok"}
    response = client.get("/traces", params={"limit": 1, "offset": 0})
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 2
    assert payload["limit"] == 1
    assert payload["offset"] == 0
    assert len(payload["items"]) == 1
    assert payload["items"][0]["trace_id"] == second.trace_id
    assert payload["items"][0]["status"] == "error"
    assert payload["items"][0]["span_count"] == 2
    assert payload["items"][0]["duration_ms"] is not None

    search_payload = client.get("/traces", params={"search": "refund"}).json()
    assert search_payload == {
        "items": [
            {
                "trace_id": second.trace_id,
                "name": "searchable-agent",
                "started_at": second.started_at.isoformat(),
                "ended_at": second.ended_at.isoformat(),
                "status": "error",
                "duration_ms": second.duration_ms,
                "span_count": 2,
            }
        ],
        "total": 1,
        "limit": 50,
        "offset": 0,
    }

    assert client.get(f"/traces/{first.trace_id}").json()["name"] == "api-agent"

    graph_payload = client.get(f"/traces/{second.trace_id}/graph").json()
    assert graph_payload["trace_id"] == second.trace_id
    assert graph_payload["edges"] == [
        {"source": second_root.span_id, "target": second.spans[1].span_id}
    ]
    assert graph_payload["likely_causes"][0]["span_id"] == second.spans[1].span_id
    assert graph_payload["nodes"][1]["error"] == "lookup failed"

    evaluation_payload = client.get(f"/traces/{second.trace_id}/evaluation").json()
    assert evaluation_payload == {
        "trace_id": second.trace_id,
        "name": "searchable-agent",
        "passed": False,
        "score": 0.5,
        "reason": "failed dimensions: correctness, safety, format",
        "dimensions": {
            "correctness": {
                "passed": False,
                "score": 0.5,
                "reason": "error spans found",
            },
            "safety": {
                "passed": False,
                "score": 0.5,
                "reason": "error spans found",
            },
            "format": {
                "passed": False,
                "score": 0.5,
                "reason": "error spans found",
            },
        },
    }

    compare_payload = client.get(
        "/traces/compare",
        params={"baseline": first.trace_id, "candidate": second.trace_id},
    ).json()
    assert compare_payload["baseline"] == {
        "trace_id": first.trace_id,
        "name": "api-agent",
        "status": "ok",
        "duration_ms": first.duration_ms,
        "span_count": 2,
        "score": 1.0,
        "passed": True,
        "failed_dimensions": [],
    }
    assert compare_payload["candidate"] == {
        "trace_id": second.trace_id,
        "name": "searchable-agent",
        "status": "error",
        "duration_ms": second.duration_ms,
        "span_count": 2,
        "score": 0.5,
        "passed": False,
        "failed_dimensions": ["correctness", "safety", "format"],
    }
    assert compare_payload["delta"]["score"] == -0.5
    assert compare_payload["delta"]["span_count"] == 0

    assert client.get("/traces/missing").status_code == 404
    assert client.get("/traces/missing/graph").status_code == 404
    assert client.get("/traces/missing/evaluation").status_code == 404
    assert client.get(
        "/traces/compare",
        params={"baseline": first.trace_id, "candidate": "missing"},
    ).status_code == 404


def test_parquet_store_reads_and_writes_with_pyarrow(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:  # type: ignore[no-untyped-def]
    written: list[dict[str, object]] = []

    class FakeTable:
        @classmethod
        def from_pylist(cls, rows: list[dict[str, object]]) -> list[dict[str, object]]:
            return rows

    fake_pq = SimpleNamespace(
        write_table=lambda rows, path: written.extend(rows),
        read_table=lambda path: SimpleNamespace(to_pylist=lambda: written),
    )
    fake_pa = SimpleNamespace(Table=FakeTable, parquet=fake_pq)
    monkeypatch.setitem(sys.modules, "pyarrow", fake_pa)
    monkeypatch.setitem(sys.modules, "pyarrow.parquet", fake_pq)

    path = tmp_path / "traces.parquet"
    path.write_text("stub")
    store = ParquetTraceStore(path)
    trace = Trace(name="arrow-agent")

    store.write_summaries([trace])

    assert store.read_summaries()[0]["trace_id"] == trace.trace_id
