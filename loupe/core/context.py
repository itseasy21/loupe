from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar, Token

from loupe.core.trace import TraceContext

_active_context: ContextVar[TraceContext | None] = ContextVar("loupe_active_context", default=None)


def get_current_context() -> TraceContext | None:
    return _active_context.get()


def set_current_context(context: TraceContext) -> Token[TraceContext | None]:
    return _active_context.set(context)


def reset_current_context(token: Token[TraceContext | None]) -> None:
    _active_context.reset(token)


@contextmanager
def use_context(context: TraceContext) -> Iterator[TraceContext]:
    token = set_current_context(context)
    try:
        yield context
    finally:
        reset_current_context(token)
