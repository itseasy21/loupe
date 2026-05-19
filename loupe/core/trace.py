from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, cast
from uuid import uuid4

JsonValue = None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject = dict[str, JsonValue]
RawObject = dict[str, Any]


class SpanKind(str, Enum):
    AGENT = "agent"
    LLM = "llm"
    TOOL = "tool"
    RETRIEVER = "retriever"
    EVALUATOR = "evaluator"


class SpanStatus(str, Enum):
    OK = "ok"
    ERROR = "error"
    UNSET = "unset"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _object(value: Any) -> JsonObject:
    return cast(JsonObject, value if isinstance(value, dict) else {})


def _objects(value: Any) -> list[RawObject]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


@dataclass(slots=True)
class TraceContext:
    trace_id: str = field(default_factory=lambda: uuid4().hex)
    span_id: str | None = None
    baggage: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> JsonObject:
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "baggage": dict(self.baggage),
        }

    @classmethod
    def from_dict(cls, data: RawObject) -> TraceContext:
        baggage = data.get("baggage", {})
        return cls(
            trace_id=str(data["trace_id"]),
            span_id=None if data.get("span_id") is None else str(data["span_id"]),
            baggage={str(key): str(value) for key, value in _object(baggage).items()},
        )


@dataclass(slots=True)
class SpanEvent:
    name: str
    timestamp: datetime = field(default_factory=utc_now)
    attributes: JsonObject = field(default_factory=dict)

    def to_dict(self) -> JsonObject:
        return {
            "name": self.name,
            "timestamp": self.timestamp.isoformat(),
            "attributes": self.attributes,
        }

    @classmethod
    def from_dict(cls, data: RawObject) -> SpanEvent:
        return cls(
            name=str(data["name"]),
            timestamp=_parse_datetime(str(data["timestamp"])),
            attributes=_object(data.get("attributes", {})),
        )


@dataclass(slots=True)
class Span:
    name: str
    kind: SpanKind
    span_id: str = field(default_factory=lambda: uuid4().hex)
    parent_id: str | None = None
    status: SpanStatus = SpanStatus.UNSET
    start_time: datetime = field(default_factory=utc_now)
    end_time: datetime | None = None
    attributes: JsonObject = field(default_factory=dict)
    inputs: JsonObject = field(default_factory=dict)
    outputs: JsonObject = field(default_factory=dict)
    events: list[SpanEvent] = field(default_factory=list)
    error: str | None = None

    @property
    def duration_ms(self) -> float | None:
        if self.end_time is None:
            return None
        return (self.end_time - self.start_time).total_seconds() * 1000

    def finish(self, status: SpanStatus = SpanStatus.OK, error: str | None = None) -> None:
        self.status = status
        self.error = error
        self.end_time = utc_now()

    def add_event(self, name: str, attributes: JsonObject | None = None) -> None:
        self.events.append(SpanEvent(name=name, attributes=attributes or {}))

    def set_outputs(self, outputs: JsonObject) -> None:
        self.outputs = outputs

    def to_dict(self) -> JsonObject:
        return {
            "span_id": self.span_id,
            "parent_id": self.parent_id,
            "name": self.name,
            "kind": self.kind.value,
            "status": self.status.value,
            "start_time": self.start_time.isoformat(),
            "end_time": None if self.end_time is None else self.end_time.isoformat(),
            "duration_ms": self.duration_ms,
            "attributes": self.attributes,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "events": [event.to_dict() for event in self.events],
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: RawObject) -> Span:
        end_time = data.get("end_time")
        return cls(
            span_id=str(data["span_id"]),
            parent_id=None if data.get("parent_id") is None else str(data["parent_id"]),
            name=str(data["name"]),
            kind=SpanKind(str(data["kind"])),
            status=SpanStatus(str(data["status"])),
            start_time=_parse_datetime(str(data["start_time"])),
            end_time=None if end_time is None else _parse_datetime(str(end_time)),
            attributes=_object(data.get("attributes", {})),
            inputs=_object(data.get("inputs", {})),
            outputs=_object(data.get("outputs", {})),
            events=[SpanEvent.from_dict(event) for event in _objects(data.get("events", []))],
            error=None if data.get("error") is None else str(data["error"]),
        )


@dataclass(slots=True)
class Trace:
    name: str
    trace_id: str = field(default_factory=lambda: uuid4().hex)
    started_at: datetime = field(default_factory=utc_now)
    ended_at: datetime | None = None
    metadata: JsonObject = field(default_factory=dict)
    spans: list[Span] = field(default_factory=list)

    @property
    def duration_ms(self) -> float | None:
        if self.ended_at is None:
            return None
        return (self.ended_at - self.started_at).total_seconds() * 1000

    def add_span(self, span: Span) -> Span:
        self.spans.append(span)
        return span

    def finish(self) -> None:
        self.ended_at = utc_now()

    def to_dict(self) -> JsonObject:
        return {
            "trace_id": self.trace_id,
            "name": self.name,
            "started_at": self.started_at.isoformat(),
            "ended_at": None if self.ended_at is None else self.ended_at.isoformat(),
            "duration_ms": self.duration_ms,
            "metadata": self.metadata,
            "spans": [span.to_dict() for span in self.spans],
        }

    @classmethod
    def from_dict(cls, data: RawObject) -> Trace:
        ended_at = data.get("ended_at")
        return cls(
            trace_id=str(data["trace_id"]),
            name=str(data["name"]),
            started_at=_parse_datetime(str(data["started_at"])),
            ended_at=None if ended_at is None else _parse_datetime(str(ended_at)),
            metadata=_object(data.get("metadata", {})),
            spans=[Span.from_dict(span) for span in _objects(data.get("spans", []))],
        )
