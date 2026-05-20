from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from loupe.core.trace import Trace


def _require_pyarrow() -> tuple[Any, Any]:
    try:
        import pyarrow as pa  # type: ignore[import-not-found]
        import pyarrow.parquet as pq  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError("Install loupe-agent[arrow] to use Parquet storage.") from exc
    return pa, pq


class ParquetTraceStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write_summaries(self, traces: list[Trace]) -> None:
        pa, pq = _require_pyarrow()
        rows = [
            {
                "trace_id": trace.trace_id,
                "name": trace.name,
                "started_at": trace.started_at.isoformat(),
                "ended_at": None if trace.ended_at is None else trace.ended_at.isoformat(),
                "span_count": len(trace.spans),
            }
            for trace in traces
        ]
        pq.write_table(pa.Table.from_pylist(rows), self.path)

    def read_summaries(self) -> list[dict[str, Any]]:
        _, pq = _require_pyarrow()
        if not self.path.exists():
            return []
        return cast(list[dict[str, Any]], pq.read_table(self.path).to_pylist())
