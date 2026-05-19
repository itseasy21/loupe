from __future__ import annotations

from collections.abc import Callable
from contextlib import ExitStack
from dataclasses import dataclass
from typing import Any
from unittest.mock import patch

from loupe.core.trace import SpanKind, Trace


@dataclass(frozen=True, slots=True)
class ReplayResult:
    trace_id: str
    returned: Any
    mocked_calls: int


class ReplayEngine:
    def replay(
        self,
        trace: Trace,
        target: Callable[..., Any],
        *args: Any,
        patches: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> ReplayResult:
        tool_outputs = {
            str(span.attributes["patch_target"]): span.outputs.get("return_value")
            for span in trace.spans
            if span.kind == SpanKind.TOOL and "patch_target" in span.attributes
        }
        if patches:
            tool_outputs.update(patches)
        with ExitStack() as stack:
            for patch_target, return_value in tool_outputs.items():
                stack.enter_context(patch(patch_target, return_value=return_value))
            returned = target(*args, **kwargs)
        return ReplayResult(
            trace_id=trace.trace_id,
            returned=returned,
            mocked_calls=len(tool_outputs),
        )
