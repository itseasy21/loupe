from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from loupe.storage.sqlite import SQLiteTraceStore

DEFAULT_DATABASE_PATH = Path(".loupe/traces.db")


@dataclass(frozen=True)
class TraceStoreConfig:
    kind: str = "sqlite"
    path: str | Path = DEFAULT_DATABASE_PATH


def create_trace_store(
    path: str | Path | None = None,
    *,
    kind: str = "sqlite",
) -> SQLiteTraceStore:
    if kind != "sqlite":
        raise ValueError(f"unsupported trace store kind: {kind}")
    return SQLiteTraceStore(DEFAULT_DATABASE_PATH if path is None else path)
