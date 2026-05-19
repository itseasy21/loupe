from __future__ import annotations

from dataclasses import dataclass

from loupe.core.trace import SpanStatus, Trace


@dataclass(frozen=True, slots=True)
class BlameScore:
    span_id: str
    name: str
    score: float
    reasons: tuple[str, ...]


def rank_failed_spans(trace: Trace) -> list[BlameScore]:
    scores: list[BlameScore] = []
    for index, span in enumerate(trace.spans):
        reasons: list[str] = []
        score = 0.0
        if span.status == SpanStatus.ERROR:
            score += 1.0
            reasons.append("span status is error")
        if span.error:
            score += 0.5
            reasons.append("span captured an exception")
        if span.parent_id is None:
            score += 0.1
            reasons.append("root span influenced downstream work")
        if score:
            adjusted_score = score - index * 0.001
            scores.append(BlameScore(span.span_id, span.name, adjusted_score, tuple(reasons)))
    return sorted(scores, key=lambda item: item.score, reverse=True)
