from __future__ import annotations

from loupe.core.context import get_current_context, use_context
from loupe.core.trace import Span, SpanKind, SpanStatus, Trace, TraceContext


def test_trace_serialization_round_trip() -> None:
    trace = Trace(name="checkout-agent", metadata={"case": "golden"})
    span = trace.add_span(Span(name="llm.plan", kind=SpanKind.LLM, inputs={"prompt": "buy milk"}))
    span.outputs = {"plan": ["search", "checkout"]}
    span.add_event("tokens", {"count": 42})
    span.finish(SpanStatus.OK)
    trace.finish()

    restored = Trace.from_dict(trace.to_dict())

    assert restored.trace_id == trace.trace_id
    assert restored.spans[0].outputs == {"plan": ["search", "checkout"]}
    assert restored.spans[0].duration_ms is not None


def test_context_is_reset_after_use() -> None:
    context = TraceContext(trace_id="trace-1", span_id="span-1")

    with use_context(context):
        assert get_current_context() == context

    assert get_current_context() is None
