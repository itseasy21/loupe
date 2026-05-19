from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from loupe.core.trace import SpanStatus, Trace


@dataclass(frozen=True, slots=True)
class JudgeResult:
    dimension: str
    passed: bool
    score: float
    reason: str


class Judge(Protocol):
    def judge(self, trace: Trace) -> JudgeResult: ...


class DeterministicJudge:
    def __init__(self, dimension: str = "overall") -> None:
        self.dimension = dimension

    def judge(self, trace: Trace) -> JudgeResult:
        if not trace.spans:
            return JudgeResult(self.dimension, False, 0.0, "trace has no spans")
        failed = [span for span in trace.spans if span.status == SpanStatus.ERROR]
        score = 1.0 - (len(failed) / len(trace.spans))
        reason = "all spans passed" if not failed else "error spans found"
        return JudgeResult(self.dimension, not failed, score, reason)
