from __future__ import annotations

import pytest

from loupe import SpanKind, SpanStatus, record
from loupe.core.context import get_current_context
from loupe.storage.sqlite import SQLiteTraceStore


def test_record_successful_span_persists_to_sqlite(tmp_path) -> None:  # type: ignore[no-untyped-def]
    database = tmp_path / "traces.db"

    recorded_trace = record("support-agent", database=database, metadata={"case": "golden"})
    with recorded_trace as trace, trace.span(
        "tool.lookup", kind="tool", inputs={"query": "refund policy"}
    ) as span:
        span.set_outputs({"result": "30-day refund window"})

    loaded = SQLiteTraceStore(database).load_trace(trace.trace_id)

    assert loaded is not None
    assert loaded.name == "support-agent"
    assert loaded.metadata == {"case": "golden"}
    assert loaded.spans[0].kind == SpanKind.TOOL
    assert loaded.spans[0].inputs == {"query": "refund policy"}
    assert loaded.spans[0].outputs == {"result": "30-day refund window"}
    assert loaded.spans[0].status == SpanStatus.OK
    assert loaded.spans[0].error is None
    assert loaded.spans[0].end_time is not None


def test_record_error_span_is_saved_and_exception_reraised(tmp_path) -> None:  # type: ignore[no-untyped-def]
    database = tmp_path / "errors.db"

    with pytest.raises(RuntimeError, match="tool failed"), record(
        "support-agent", database=database
    ) as trace, trace.span("tool.lookup", kind=SpanKind.TOOL):
        raise RuntimeError("tool failed")

    loaded = SQLiteTraceStore(database).load_trace(trace.trace_id)

    assert loaded is not None
    assert loaded.spans[0].status == SpanStatus.ERROR
    assert loaded.spans[0].error == "RuntimeError: tool failed"
    assert loaded.spans[0].end_time is not None


def test_record_nested_spans_use_parent_id(tmp_path) -> None:  # type: ignore[no-untyped-def]
    database = tmp_path / "nested.db"

    with record("support-agent", database=database) as trace, trace.span(
        "agent.run", kind=SpanKind.AGENT
    ) as parent, trace.span("tool.lookup", kind=SpanKind.TOOL) as child:
        child.set_outputs({"result": "ok"})

    assert child.parent_id == parent.span_id
    loaded = SQLiteTraceStore(database).load_trace(trace.trace_id)
    assert loaded is not None
    assert loaded.spans[1].parent_id == loaded.spans[0].span_id


def test_record_sets_and_resets_context(tmp_path) -> None:  # type: ignore[no-untyped-def]
    database = tmp_path / "context.db"

    assert get_current_context() is None
    with record("support-agent", database=database) as trace:
        trace_context = get_current_context()
        assert trace_context is not None
        assert trace_context.trace_id == trace.trace_id
        assert trace_context.span_id is None

        with trace.span("tool.lookup", kind=SpanKind.TOOL) as span:
            span_context = get_current_context()
            assert span_context is not None
            assert span_context.trace_id == trace.trace_id
            assert span_context.span_id == span.span_id

        restored_context = get_current_context()
        assert restored_context is not None
        assert restored_context.trace_id == trace.trace_id
        assert restored_context.span_id is None

    assert get_current_context() is None
