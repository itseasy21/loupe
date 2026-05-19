from __future__ import annotations

from pathlib import Path
from typing import Any

from loupe.core.trace import JsonObject, JsonValue, Span, SpanKind, SpanStatus, Trace
from loupe.storage import DEFAULT_DATABASE_PATH, create_trace_store


def _json_value(value: Any) -> JsonValue:
    if value is None or isinstance(value, bool | int | float | str):
        return value
    if isinstance(value, list | tuple):
        return [_json_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    return str(value)


def _json_object(value: Any) -> JsonObject:
    converted = _json_value(value)
    return converted if isinstance(converted, dict) else {"value": converted}


def _run_key(run_id: Any) -> str:
    return str(run_id)


class LoupeCallbackHandler:
    def __init__(
        self,
        trace_name: str = "langchain-run",
        *,
        database: str | Path = DEFAULT_DATABASE_PATH,
        metadata: JsonObject | None = None,
        auto_save: bool = True,
    ) -> None:
        self.trace = Trace(name=trace_name, metadata=metadata or {})
        self.database = Path(database)
        self.auto_save = auto_save
        self._spans: dict[str, Span] = {}

    def on_chain_start(
        self,
        serialized: dict[str, Any],
        inputs: dict[str, Any],
        run_id: Any,
        *,
        parent_run_id: Any = None,
        **_: Any,
    ) -> None:
        self._start_span(
            run_id,
            parent_run_id,
            name=str(serialized.get("name", "chain")),
            kind=SpanKind.AGENT,
            inputs=inputs,
        )

    def on_chain_end(self, outputs: dict[str, Any], run_id: Any, **_: Any) -> None:
        self._finish_span(run_id, outputs=outputs)

    def on_chain_error(self, error: BaseException, run_id: Any, **_: Any) -> None:
        self._finish_span(run_id, status=SpanStatus.ERROR, error=error)

    def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        run_id: Any,
        *,
        parent_run_id: Any = None,
        **_: Any,
    ) -> None:
        self._start_span(
            run_id,
            parent_run_id,
            name=str(serialized.get("name", "llm")),
            kind=SpanKind.LLM,
            inputs={"prompts": prompts},
        )

    def on_llm_end(self, response: Any, run_id: Any, **_: Any) -> None:
        self._finish_span(run_id, outputs=_json_object(response))

    def on_llm_error(self, error: BaseException, run_id: Any, **_: Any) -> None:
        self._finish_span(run_id, status=SpanStatus.ERROR, error=error)

    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        run_id: Any,
        *,
        parent_run_id: Any = None,
        **_: Any,
    ) -> None:
        self._start_span(
            run_id,
            parent_run_id,
            name=str(serialized.get("name", "tool")),
            kind=SpanKind.TOOL,
            inputs={"input": input_str},
        )

    def on_tool_end(self, output: Any, run_id: Any, **_: Any) -> None:
        self._finish_span(run_id, outputs={"output": _json_value(output)})

    def on_tool_error(self, error: BaseException, run_id: Any, **_: Any) -> None:
        self._finish_span(run_id, status=SpanStatus.ERROR, error=error)

    def save(self) -> None:
        self.trace.finish()
        create_trace_store(self.database).save_trace(self.trace)

    def _start_span(
        self,
        run_id: Any,
        parent_run_id: Any,
        *,
        name: str,
        kind: SpanKind,
        inputs: dict[str, Any],
    ) -> None:
        parent = self._spans.get(_run_key(parent_run_id)) if parent_run_id is not None else None
        span = Span(
            name=name,
            kind=kind,
            parent_id=None if parent is None else parent.span_id,
            inputs=_json_object(inputs),
            attributes={"run_id": _run_key(run_id)},
        )
        self._spans[_run_key(run_id)] = self.trace.add_span(span)

    def _finish_span(
        self,
        run_id: Any,
        *,
        outputs: dict[str, Any] | None = None,
        status: SpanStatus = SpanStatus.OK,
        error: BaseException | None = None,
    ) -> None:
        span = self._spans.get(_run_key(run_id))
        if span is None:
            return
        if outputs is not None:
            span.set_outputs(_json_object(outputs))
        span.finish(status, None if error is None else f"{type(error).__name__}: {error}")
        if self.auto_save:
            self.save()
