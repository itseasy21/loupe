from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from loupe.core.trace import Trace
from loupe.eval.judge import DeterministicJudge, Judge, JudgeResult


@dataclass(frozen=True, slots=True)
class DimensionResult:
    passed: bool
    score: float
    reason: str


@dataclass(frozen=True, slots=True)
class EvaluationResult:
    passed: bool
    score: float
    reason: str
    dimensions: dict[str, DimensionResult] = field(default_factory=dict)


class Evaluator(Protocol):
    def evaluate(self, trace: Trace) -> EvaluationResult: ...


class DeterministicEvaluator:
    def __init__(self, judges: list[Judge] | None = None) -> None:
        self.judges = judges or [
            DeterministicJudge("correctness"),
            DeterministicJudge("safety"),
            DeterministicJudge("format"),
        ]

    def evaluate(self, trace: Trace) -> EvaluationResult:
        results = [judge.judge(trace) for judge in self.judges]
        dimensions = {result.dimension: _dimension_result(result) for result in results}
        score = sum(result.score for result in results) / len(results)
        passed = all(result.passed for result in results)
        reason = _overall_reason(results)
        return EvaluationResult(passed, score, reason, dimensions)


def _dimension_result(result: JudgeResult) -> DimensionResult:
    return DimensionResult(result.passed, result.score, result.reason)


def _overall_reason(results: list[JudgeResult]) -> str:
    failed = [result.dimension for result in results if not result.passed]
    return "all dimensions passed" if not failed else f"failed dimensions: {', '.join(failed)}"
