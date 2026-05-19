from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from loupe.core.trace import SpanStatus, Trace
from loupe.eval.evaluator import EvaluationResult

CURRENT_SCHEMA_VERSION = 1


class SQLiteTraceStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            version = int(connection.execute("PRAGMA user_version").fetchone()[0])
            if version > CURRENT_SCHEMA_VERSION:
                raise RuntimeError("SQLite store was created by a newer Loupe version")
            if version == 0:
                self._create_schema(connection)
                connection.execute(f"PRAGMA user_version = {CURRENT_SCHEMA_VERSION}")

    def _create_schema(self, connection: sqlite3.Connection) -> None:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS traces (
                trace_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                started_at TEXT NOT NULL,
                ended_at TEXT,
                payload TEXT NOT NULL
            )
            """
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_traces_started_at ON traces(started_at)"
        )

    def save_trace(self, trace: Trace) -> None:
        payload = json.dumps(trace.to_dict(), sort_keys=True)
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO traces(trace_id, name, started_at, ended_at, payload)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(trace_id) DO UPDATE SET
                    name = excluded.name,
                    started_at = excluded.started_at,
                    ended_at = excluded.ended_at,
                    payload = excluded.payload
                """,
                (
                    trace.trace_id,
                    trace.name,
                    trace.started_at.isoformat(),
                    None if trace.ended_at is None else trace.ended_at.isoformat(),
                    payload,
                ),
            )

    def load_trace(self, trace_id: str) -> Trace | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload FROM traces WHERE trace_id = ?", (trace_id,)
            ).fetchone()
        if row is None:
            return None
        return Trace.from_dict(json.loads(str(row["payload"])))

    def _summarize_trace(self, row: sqlite3.Row) -> dict[str, Any]:
        trace = Trace.from_dict(json.loads(str(row["payload"])))
        status = SpanStatus.OK.value
        if any(span.status == SpanStatus.ERROR for span in trace.spans):
            status = SpanStatus.ERROR.value
        elif any(span.status == SpanStatus.UNSET for span in trace.spans):
            status = SpanStatus.UNSET.value
        return {
            "trace_id": row["trace_id"],
            "name": row["name"],
            "started_at": row["started_at"],
            "ended_at": row["ended_at"],
            "status": status,
            "duration_ms": trace.duration_ms,
            "span_count": len(trace.spans),
        }

    def list_traces(self, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT trace_id, name, started_at, ended_at, payload
                FROM traces
                ORDER BY started_at DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            ).fetchall()
        return [self._summarize_trace(row) for row in rows]

    def count_traces(self) -> int:
        with self._connect() as connection:
            return int(connection.execute("SELECT COUNT(*) FROM traces").fetchone()[0])

    def search_traces(self, query: str, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        pattern = f"%{query.lower()}%"
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT trace_id, name, started_at, ended_at, payload
                FROM traces
                WHERE lower(name) LIKE ? OR lower(payload) LIKE ?
                ORDER BY started_at DESC
                LIMIT ? OFFSET ?
                """,
                (pattern, pattern, limit, offset),
            ).fetchall()
        return [self._summarize_trace(row) for row in rows]

    def count_search_traces(self, query: str) -> int:
        pattern = f"%{query.lower()}%"
        with self._connect() as connection:
            return int(
                connection.execute(
                    """
                    SELECT COUNT(*)
                    FROM traces
                    WHERE lower(name) LIKE ? OR lower(payload) LIKE ?
                    """,
                    (pattern, pattern),
                ).fetchone()[0]
            )

    def build_causal_graph_payload(self, trace_id: str) -> dict[str, Any] | None:
        trace = self.load_trace(trace_id)
        if trace is None:
            return None

        from loupe.causal.attributor import rank_failed_spans
        from loupe.causal.graph import build_causal_graph

        graph = build_causal_graph(trace)
        nodes = [
            {
                "span_id": span.span_id,
                "parent_id": span.parent_id,
                "name": span.name,
                "kind": span.kind.value,
                "status": span.status.value,
                "duration_ms": span.duration_ms,
                "error": span.error,
            }
            for span in trace.spans
        ]
        edges = [
            {"source": parent_id, "target": child_id}
            for parent_id, child_ids in graph.edges.items()
            for child_id in sorted(child_ids)
        ]
        likely_causes = [
            {
                "span_id": score.span_id,
                "name": score.name,
                "score": score.score,
                "reasons": list(score.reasons),
            }
            for score in rank_failed_spans(trace)
        ]
        return {
            "trace_id": trace.trace_id,
            "name": trace.name,
            "nodes": nodes,
            "edges": edges,
            "likely_causes": likely_causes,
        }

    def build_evaluation_summary(self, trace_id: str) -> dict[str, Any] | None:
        trace = self.load_trace(trace_id)
        if trace is None:
            return None

        from loupe.eval.evaluator import DeterministicEvaluator

        result = DeterministicEvaluator().evaluate(trace)
        return {
            "trace_id": trace.trace_id,
            "name": trace.name,
            "passed": result.passed,
            "score": result.score,
            "reason": result.reason,
            "dimensions": {
                dimension: {
                    "passed": payload.passed,
                    "score": payload.score,
                    "reason": payload.reason,
                }
                for dimension, payload in result.dimensions.items()
            },
        }

    def compare_traces(
        self, baseline_trace_id: str, candidate_trace_id: str
    ) -> dict[str, Any] | None:
        baseline = self.load_trace(baseline_trace_id)
        candidate = self.load_trace(candidate_trace_id)
        if baseline is None or candidate is None:
            return None

        from loupe.eval.evaluator import DeterministicEvaluator

        baseline_evaluation = DeterministicEvaluator().evaluate(baseline)
        candidate_evaluation = DeterministicEvaluator().evaluate(candidate)
        return {
            "baseline": self._comparison_trace_payload(baseline, baseline_evaluation),
            "candidate": self._comparison_trace_payload(candidate, candidate_evaluation),
            "delta": {
                "score": candidate_evaluation.score - baseline_evaluation.score,
                "span_count": len(candidate.spans) - len(baseline.spans),
                "duration_ms": _delta_duration_ms(candidate.duration_ms, baseline.duration_ms),
            },
        }

    def _comparison_trace_payload(
        self, trace: Trace, evaluation: EvaluationResult
    ) -> dict[str, Any]:
        return {
            "trace_id": trace.trace_id,
            "name": trace.name,
            "status": self._trace_status(trace),
            "duration_ms": trace.duration_ms,
            "span_count": len(trace.spans),
            "score": evaluation.score,
            "passed": evaluation.passed,
            "failed_dimensions": [
                dimension
                for dimension, payload in evaluation.dimensions.items()
                if not payload.passed
            ],
        }

    def _trace_status(self, trace: Trace) -> str:
        if any(span.status == SpanStatus.ERROR for span in trace.spans):
            return SpanStatus.ERROR.value
        if any(span.status == SpanStatus.UNSET for span in trace.spans):
            return SpanStatus.UNSET.value
        return SpanStatus.OK.value


def _delta_duration_ms(
    candidate_duration: float | None, baseline_duration: float | None
) -> float | None:
    if candidate_duration is None or baseline_duration is None:
        return None
    return candidate_duration - baseline_duration
