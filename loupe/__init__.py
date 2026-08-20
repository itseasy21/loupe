"""Loupe: inspect what your agent actually did."""

from loupe.core.trace import Span, SpanEvent, SpanKind, SpanStatus, Trace, TraceContext
from loupe.sdk import RecordedTrace, record
from loupe.storage import DEFAULT_DATABASE_PATH

__all__ = [
    "Span",
    "SpanEvent",
    "SpanKind",
    "SpanStatus",
    "Trace",
    "TraceContext",
    "DEFAULT_DATABASE_PATH",
    "RecordedTrace",
    "record",
]

__version__ = "0.2.0"
