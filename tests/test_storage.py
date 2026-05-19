from __future__ import annotations

import json
import sys

import pytest
from typer.testing import CliRunner

from loupe import __version__
from loupe.cli.main import app
from loupe.core.trace import Span, SpanKind, SpanStatus, Trace
from loupe.storage import DEFAULT_DATABASE_PATH, create_trace_store
from loupe.storage.arrow import ParquetTraceStore
from loupe.storage.sqlite import CURRENT_SCHEMA_VERSION, SQLiteTraceStore


def test_sqlite_store_save_load_and_list(tmp_path) -> None:  # type: ignore[no-untyped-def]
    database = tmp_path / "traces.db"
    store = SQLiteTraceStore(database)
    trace = Trace(name="support-agent")
    trace.add_span(Span(name="tool.lookup", kind=SpanKind.TOOL, status=SpanStatus.OK))
    trace.finish()

    store.save_trace(trace)

    loaded = store.load_trace(trace.trace_id)
    assert loaded is not None
    assert loaded.name == "support-agent"
    assert store.list_traces()[0] == {
        "trace_id": trace.trace_id,
        "name": "support-agent",
        "started_at": trace.started_at.isoformat(),
        "ended_at": trace.ended_at.isoformat(),
        "status": "ok",
        "duration_ms": trace.duration_ms,
        "span_count": 1,
    }


def test_cli_record_demo_creates_trace(tmp_path) -> None:  # type: ignore[no-untyped-def]
    database = tmp_path / "cli.db"
    runner = CliRunner()

    result = runner.invoke(app, ["record-demo", "--database", str(database)])

    assert result.exit_code == 0
    trace_id = result.stdout.strip()
    assert SQLiteTraceStore(database).load_trace(trace_id) is not None


def test_cli_record_runs_command_and_persists_trace(tmp_path) -> None:  # type: ignore[no-untyped-def]
    database = tmp_path / "record.db"
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "record",
            "--name",
            "smoke-test",
            "--database",
            str(database),
            "--metadata",
            "case=golden",
            "python",
            "-c",
            "print('hello')",
        ],
    )

    assert result.exit_code == 0
    trace = SQLiteTraceStore(database).load_trace(result.stdout.strip())
    assert trace is not None
    assert trace.name == "smoke-test"
    assert trace.metadata == {"source": "loupe-cli", "case": "golden"}
    assert trace.spans[0].name == "process.run"
    assert trace.spans[0].status == SpanStatus.OK
    assert trace.spans[0].outputs["returncode"] == 0
    assert trace.spans[0].outputs["stdout"] == "hello\n"


def test_cli_record_nonzero_command_persists_error_trace(tmp_path) -> None:  # type: ignore[no-untyped-def]
    database = tmp_path / "record-error.db"
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "record",
            "--name",
            "smoke-test",
            "--database",
            str(database),
            "python",
            "-c",
            "raise SystemExit(3)",
        ],
    )

    assert result.exit_code == 3
    trace = SQLiteTraceStore(database).list_traces()[0]
    loaded = SQLiteTraceStore(database).load_trace(trace["trace_id"])
    assert loaded is not None
    assert loaded.spans[0].status == SpanStatus.ERROR
    assert loaded.spans[0].outputs["returncode"] == 3


def test_cli_record_missing_command_persists_error_trace(tmp_path) -> None:  # type: ignore[no-untyped-def]
    database = tmp_path / "record-missing.db"
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "record",
            "--name",
            "missing-command",
            "--database",
            str(database),
            "loupe-command-that-does-not-exist",
        ],
    )

    assert result.exit_code == 127
    trace = SQLiteTraceStore(database).list_traces()[0]
    loaded = SQLiteTraceStore(database).load_trace(trace["trace_id"])
    assert loaded is not None
    assert loaded.spans[0].status == SpanStatus.ERROR
    assert loaded.spans[0].outputs["returncode"] == 127
    assert "FileNotFoundError" in str(loaded.spans[0].outputs["stderr"])
    assert "FileNotFoundError" in str(loaded.spans[0].error)


def test_cli_record_truncates_large_output(tmp_path) -> None:  # type: ignore[no-untyped-def]
    database = tmp_path / "record-large.db"
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "record",
            "--name",
            "large-output",
            "--database",
            str(database),
            "python",
            "-c",
            "print('x' * 70000)",
        ],
    )

    assert result.exit_code == 0
    trace = SQLiteTraceStore(database).load_trace(result.stdout.strip())
    assert trace is not None
    stdout = str(trace.spans[0].outputs["stdout"])
    assert len(stdout) < 70000
    assert "truncated" in stdout


def test_cli_record_defaults_name_to_command_basename(tmp_path) -> None:  # type: ignore[no-untyped-def]
    database = tmp_path / "record-default-name.db"
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "record",
            "--database",
            str(database),
            "python",
            "-c",
            "print('hello')",
        ],
    )

    assert result.exit_code == 0
    trace = SQLiteTraceStore(database).load_trace(result.stdout.strip())
    assert trace is not None
    assert trace.name == "python"


def test_cli_record_allows_command_options(tmp_path) -> None:  # type: ignore[no-untyped-def]
    database = tmp_path / "record-options.db"
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "record",
            "--database",
            str(database),
            "python",
            "--version",
        ],
    )

    assert result.exit_code == 0
    trace = SQLiteTraceStore(database).load_trace(result.stdout.strip())
    assert trace is not None
    assert trace.spans[0].outputs["returncode"] == 0


def test_cli_record_preserves_child_options_matching_loupe_options(tmp_path) -> None:  # type: ignore[no-untyped-def]
    database = tmp_path / "record-child-options.db"
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "record",
            "--database",
            str(database),
            "python",
            "-c",
            "import sys; print(sys.argv[1:])",
            "--name",
            "child",
            "--metadata",
            "child=value",
        ],
    )

    assert result.exit_code == 0
    trace = SQLiteTraceStore(database).load_trace(result.stdout.strip())
    assert trace is not None
    assert trace.name == "python"
    assert trace.metadata == {"source": "loupe-cli"}
    assert trace.spans[0].outputs["stdout"] == "['--name', 'child', '--metadata', 'child=value']\n"


def test_sqlite_initializes_schema_version(tmp_path) -> None:  # type: ignore[no-untyped-def]
    database = tmp_path / "schema.db"

    SQLiteTraceStore(database)

    with create_trace_store(database)._connect() as connection:
        version = connection.execute("PRAGMA user_version").fetchone()[0]
    assert version == CURRENT_SCHEMA_VERSION


def test_sqlite_rejects_newer_schema_version(tmp_path) -> None:  # type: ignore[no-untyped-def]
    database = tmp_path / "future.db"
    with create_trace_store(database)._connect() as connection:
        connection.execute(f"PRAGMA user_version = {CURRENT_SCHEMA_VERSION + 1}")

    with pytest.raises(RuntimeError, match="newer Loupe version"):
        SQLiteTraceStore(database)


def test_create_trace_store_uses_default_and_explicit_sqlite_paths(tmp_path) -> None:  # type: ignore[no-untyped-def]
    database = tmp_path / "factory.db"

    explicit = create_trace_store(database)
    default = create_trace_store()

    assert isinstance(explicit, SQLiteTraceStore)
    assert explicit.path == database
    assert default.path == DEFAULT_DATABASE_PATH


def test_create_trace_store_rejects_unsupported_kind(tmp_path) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(ValueError, match="unsupported trace store kind"):
        create_trace_store(tmp_path / "traces.db", kind="parquet")


def test_sqlite_search_matches_trace_and_span_payload(tmp_path) -> None:  # type: ignore[no-untyped-def]
    database = tmp_path / "search.db"
    store = SQLiteTraceStore(database)

    first = Trace(name="support-agent")
    first_span = first.add_span(
        Span(
            name="tool.lookup",
            kind=SpanKind.TOOL,
            inputs={"query": "refund policy"},
            outputs={"result": "30-day refund window"},
        )
    )
    first_span.finish()
    first.finish()
    store.save_trace(first)

    second = Trace(name="billing-agent")
    second.add_span(Span(name="tool.lookup", kind=SpanKind.TOOL, status=SpanStatus.OK))
    second.finish()
    store.save_trace(second)

    assert store.search_traces("support")[0]["trace_id"] == first.trace_id
    assert store.search_traces("refund")[0]["trace_id"] == first.trace_id
    assert [item["trace_id"] for item in store.list_traces(limit=1, offset=1)] == [first.trace_id]
    assert [
        item["trace_id"] for item in store.search_traces("agent", limit=1, offset=1)
    ] == [first.trace_id]
    assert store.count_traces() == 2
    assert store.count_search_traces("agent") == 2
    assert store.count_search_traces("refund") == 1
    assert store.search_traces("missing") == []


def test_sqlite_builds_analysis_payloads(tmp_path) -> None:  # type: ignore[no-untyped-def]
    database = tmp_path / "analysis.db"
    store = SQLiteTraceStore(database)

    baseline = Trace(name="baseline-agent")
    baseline_root = baseline.add_span(
        Span(name="agent.run", kind=SpanKind.AGENT, status=SpanStatus.OK)
    )
    baseline.add_span(
        Span(
            name="tool.lookup",
            kind=SpanKind.TOOL,
            parent_id=baseline_root.span_id,
            status=SpanStatus.OK,
        )
    )
    baseline.finish()
    store.save_trace(baseline)

    candidate = Trace(name="candidate-agent")
    candidate_root = candidate.add_span(
        Span(name="agent.run", kind=SpanKind.AGENT, status=SpanStatus.OK)
    )
    candidate.add_span(
        Span(
            name="tool.lookup",
            kind=SpanKind.TOOL,
            parent_id=candidate_root.span_id,
            status=SpanStatus.ERROR,
            error="lookup failed",
        )
    )
    candidate.finish()
    store.save_trace(candidate)

    graph_payload = store.build_causal_graph_payload(candidate.trace_id)
    assert graph_payload is not None
    assert graph_payload["trace_id"] == candidate.trace_id
    assert graph_payload["nodes"][0]["span_id"] == candidate_root.span_id
    assert graph_payload["edges"] == [
        {"source": candidate_root.span_id, "target": candidate.spans[1].span_id}
    ]
    assert graph_payload["likely_causes"][0]["reasons"] == [
        "span status is error",
        "span captured an exception",
    ]

    evaluation_payload = store.build_evaluation_summary(candidate.trace_id)
    assert evaluation_payload is not None
    assert evaluation_payload["passed"] is False
    assert evaluation_payload["score"] == 0.5
    assert evaluation_payload["dimensions"]["correctness"]["reason"] == "error spans found"

    compare_payload = store.compare_traces(baseline.trace_id, candidate.trace_id)
    assert compare_payload is not None
    assert compare_payload["baseline"]["trace_id"] == baseline.trace_id
    assert compare_payload["candidate"]["trace_id"] == candidate.trace_id
    assert compare_payload["candidate"]["failed_dimensions"] == ["correctness", "safety", "format"]
    assert compare_payload["delta"]["score"] == -0.5
    assert compare_payload["delta"]["span_count"] == 0
    assert compare_payload["delta"]["duration_ms"] is not None

    assert store.build_causal_graph_payload("missing") is None
    assert store.build_evaluation_summary("missing") is None
    assert store.compare_traces(baseline.trace_id, "missing") is None


def test_cli_show_outputs_json_and_search_finds_payload(tmp_path) -> None:  # type: ignore[no-untyped-def]
    database = tmp_path / "cli-search.db"
    runner = CliRunner()
    trace = Trace(name="support-agent")
    span = trace.add_span(
        Span(
            name="tool.lookup",
            kind=SpanKind.TOOL,
            inputs={"query": "refund policy"},
            outputs={"result": "30-day refund window"},
        )
    )
    span.finish()
    trace.finish()
    SQLiteTraceStore(database).save_trace(trace)

    show_result = runner.invoke(app, ["show", trace.trace_id, "--database", str(database)])
    search_result = runner.invoke(app, ["search", "refund", "--database", str(database)])

    assert show_result.exit_code == 0
    assert json.loads(show_result.stdout)["trace_id"] == trace.trace_id
    assert search_result.exit_code == 0
    assert trace.trace_id in search_result.stdout


def test_cli_inspect_outputs_nested_span_tree(tmp_path) -> None:  # type: ignore[no-untyped-def]
    database = tmp_path / "inspect.db"
    runner = CliRunner()
    trace = Trace(name="support-agent")
    root = trace.add_span(
        Span(
            name="agent.run",
            kind=SpanKind.AGENT,
            inputs={"prompt": "refund policy"},
        )
    )
    child = trace.add_span(
        Span(
            name="tool.lookup",
            kind=SpanKind.TOOL,
            parent_id=root.span_id,
            outputs={"result": "30-day refund window"},
        )
    )
    root.finish()
    child.finish(SpanStatus.ERROR, "lookup failed")
    trace.finish()
    SQLiteTraceStore(database).save_trace(trace)

    result = runner.invoke(app, ["inspect", trace.trace_id, "--database", str(database)])

    assert result.exit_code == 0
    assert "Trace: support-agent" in result.stdout
    assert f"ID: {trace.trace_id}" in result.stdout
    assert "Status: error" in result.stdout
    assert "  - agent.run (agent, ok," in result.stdout
    assert '    inputs: {"prompt": "refund policy"}' in result.stdout
    assert "    - tool.lookup (tool, error," in result.stdout
    assert '      outputs: {"result": "30-day refund window"}' in result.stdout
    assert '      error: "lookup failed"' in result.stdout


def test_cli_info_reports_store_details(tmp_path) -> None:  # type: ignore[no-untyped-def]
    database = tmp_path / "info.db"
    runner = CliRunner()
    trace = Trace(name="support-agent")
    SQLiteTraceStore(database).save_trace(trace)

    result = runner.invoke(app, ["info", "--database", str(database)])

    assert result.exit_code == 0
    assert f"version: {__version__}" in result.stdout
    assert "default_database: .loupe/traces.db" in result.stdout
    assert f"database: {database}" in result.stdout
    assert "trace_count: 1" in result.stdout
    assert "LoupeCallbackHandler" in result.stdout


def test_cli_replay_prints_stored_tool_outputs(tmp_path) -> None:  # type: ignore[no-untyped-def]
    database = tmp_path / "replay.db"
    runner = CliRunner()
    trace = Trace(name="replay-agent")
    span = trace.add_span(
        Span(
            name="tool.lookup",
            kind=SpanKind.TOOL,
            outputs={"return_value": {"answer": "recorded"}},
        )
    )
    span.finish()
    trace.finish()
    SQLiteTraceStore(database).save_trace(trace)

    result = runner.invoke(app, ["replay", trace.trace_id, "--database", str(database)])

    assert result.exit_code == 0
    assert '{"answer": "recorded"}' in result.stdout


def test_cli_evaluate_scores_trace(tmp_path) -> None:  # type: ignore[no-untyped-def]
    database = tmp_path / "evaluate.db"
    runner = CliRunner()
    trace = Trace(name="failed-agent")
    trace.add_span(Span(name="ok", kind=SpanKind.AGENT, status=SpanStatus.OK))
    trace.add_span(Span(name="bad", kind=SpanKind.TOOL, status=SpanStatus.ERROR))
    SQLiteTraceStore(database).save_trace(trace)

    result = runner.invoke(app, ["evaluate", trace.trace_id, "--database", str(database)])

    assert result.exit_code == 0
    assert "score: 0.50" in result.stdout
    assert "label: fail" in result.stdout
    assert "reason: failed dimensions: correctness, safety, format" in result.stdout
    assert "dimension[correctness]: score=0.50 label=fail reason=error spans found" in result.stdout
    assert "dimension[safety]: score=0.50 label=fail reason=error spans found" in result.stdout
    assert "dimension[format]: score=0.50 label=fail reason=error spans found" in result.stdout


def test_cli_evaluate_empty_trace_fails(tmp_path) -> None:  # type: ignore[no-untyped-def]
    database = tmp_path / "evaluate-empty.db"
    runner = CliRunner()
    trace = Trace(name="empty-agent")
    SQLiteTraceStore(database).save_trace(trace)

    result = runner.invoke(app, ["evaluate", trace.trace_id, "--database", str(database)])

    assert result.exit_code == 0
    assert "score: 0.00" in result.stdout
    assert "label: fail" in result.stdout
    assert "reason: failed dimensions: correctness, safety, format" in result.stdout
    assert (
        "dimension[correctness]: score=0.00 label=fail reason=trace has no spans"
        in result.stdout
    )
    assert "dimension[safety]: score=0.00 label=fail reason=trace has no spans" in result.stdout
    assert "dimension[format]: score=0.00 label=fail reason=trace has no spans" in result.stdout


def test_cli_graph_outputs_causal_tree_and_likely_causes(tmp_path) -> None:  # type: ignore[no-untyped-def]
    database = tmp_path / "graph.db"
    runner = CliRunner()
    trace = Trace(name="failed-agent")
    root = trace.add_span(Span(name="agent", kind=SpanKind.AGENT))
    child = trace.add_span(Span(name="tool.lookup", kind=SpanKind.TOOL, parent_id=root.span_id))
    child.finish(SpanStatus.ERROR, "boom")
    trace.finish()
    SQLiteTraceStore(database).save_trace(trace)

    result = runner.invoke(app, ["graph", trace.trace_id, "--database", str(database)])

    assert result.exit_code == 0
    assert f"Trace {trace.trace_id} (failed-agent)" in result.stdout
    assert f"- {root.span_id} agent [unset]" in result.stdout
    assert f"  - {child.span_id} tool.lookup [error]" in result.stdout
    assert "Likely causes:" in result.stdout
    assert f"- {child.span_id} tool.lookup score=1.499" in result.stdout


def test_cli_graph_exports_svg(tmp_path) -> None:  # type: ignore[no-untyped-def]
    database = tmp_path / "graph-export.db"
    output = tmp_path / "graph.svg"
    runner = CliRunner()
    trace = Trace(name="support-agent")
    root = trace.add_span(Span(name="agent.run", kind=SpanKind.AGENT))
    child = trace.add_span(Span(name="tool.lookup", kind=SpanKind.TOOL, parent_id=root.span_id))
    child.finish()
    root.finish()
    trace.finish()
    SQLiteTraceStore(database).save_trace(trace)

    result = runner.invoke(
        app,
        ["graph", trace.trace_id, "--database", str(database), "--output", str(output)],
    )

    assert result.exit_code == 0
    assert f"Trace {trace.trace_id} (support-agent)" in result.stdout
    assert f"Exported graph to {output}" in result.stdout
    svg = output.read_text(encoding="utf-8")
    assert "<svg" in svg
    assert "agent.run" in svg
    assert "tool.lookup" in svg


def test_cli_graph_png_output_writes_requested_path(tmp_path) -> None:  # type: ignore[no-untyped-def]
    database = tmp_path / "graph-png.db"
    output = tmp_path / "graph.png"
    runner = CliRunner()
    trace = Trace(name="support-agent")
    trace.add_span(Span(name="agent.run", kind=SpanKind.AGENT))
    trace.finish()
    SQLiteTraceStore(database).save_trace(trace)

    result = runner.invoke(
        app,
        ["graph", trace.trace_id, "--database", str(database), "--output", str(output)],
    )

    assert result.exit_code == 0
    assert f"Exported graph to {output}" in result.stdout
    assert output.exists()
    assert "<svg" in output.read_text(encoding="utf-8")


def test_parquet_store_requires_optional_dependency(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:  # type: ignore[no-untyped-def]
    original_import = __import__

    def blocked_import(name: str, *args: object, **kwargs: object) -> object:
        if name.startswith("pyarrow"):
            raise ImportError(name)
        return original_import(name, *args, **kwargs)

    monkeypatch.delitem(sys.modules, "pyarrow", raising=False)
    monkeypatch.delitem(sys.modules, "pyarrow.parquet", raising=False)
    monkeypatch.setattr("builtins.__import__", blocked_import)

    with pytest.raises(RuntimeError, match=r"loupe\[arrow\]"):
        ParquetTraceStore(tmp_path / "traces.parquet").read_summaries()
