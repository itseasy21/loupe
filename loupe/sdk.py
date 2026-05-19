from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import Token
from pathlib import Path
from types import TracebackType

from loupe.core.context import reset_current_context, set_current_context
from loupe.core.trace import JsonObject, Span, SpanKind, SpanStatus, Trace, TraceContext
from loupe.storage import DEFAULT_DATABASE_PATH, create_trace_store


class RecordedTrace:
    def __init__(
        self,
        name: str,
        *,
        database: str | Path = DEFAULT_DATABASE_PATH,
        metadata: JsonObject | None = None,
    ) -> None:
        self.trace = Trace(name=name, metadata=metadata or {})
        self.database = Path(database)
        self._context_token: Token[TraceContext | None] | None = None
        self._span_stack: list[Span] = []

    @property
    def trace_id(self) -> str:
        return self.trace.trace_id

    def __enter__(self) -> RecordedTrace:
        token = set_current_context(TraceContext(trace_id=self.trace_id))
        self._context_token = token
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.trace.finish()
        create_trace_store(self.database).save_trace(self.trace)
        if self._context_token is not None:
            reset_current_context(self._context_token)

    @contextmanager
    def span(
        self,
        name: str,
        *,
        kind: str | SpanKind = SpanKind.AGENT,
        inputs: JsonObject | None = None,
        attributes: JsonObject | None = None,
    ) -> Iterator[Span]:
        parent = self._span_stack[-1] if self._span_stack else None
        span = self.trace.add_span(
            Span(
                name=name,
                kind=SpanKind(kind),
                parent_id=None if parent is None else parent.span_id,
                inputs=inputs or {},
                attributes=attributes or {},
            )
        )
        token = set_current_context(
            TraceContext(trace_id=self.trace_id, span_id=span.span_id)
        )
        self._span_stack.append(span)
        try:
            yield span
        except Exception as error:
            span.finish(SpanStatus.ERROR, error=f"{type(error).__name__}: {error}")
            raise
        else:
            span.finish(SpanStatus.OK)
        finally:
            self._span_stack.pop()
            reset_current_context(token)


def record(
    name: str,
    *,
    database: str | Path = DEFAULT_DATABASE_PATH,
    metadata: JsonObject | None = None,
) -> RecordedTrace:
    return RecordedTrace(name, database=database, metadata=metadata)
