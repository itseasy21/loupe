from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException

from loupe.storage import create_trace_store
from loupe.storage.sqlite import SQLiteTraceStore


def create_app(database_path: str | Path = ".loupe/traces.db") -> FastAPI:
    app = FastAPI(title="Loupe API", version="0.1.0")
    store = create_trace_store(database_path)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/traces")
    def list_traces(limit: int = 50, offset: int = 0, search: str | None = None) -> dict[str, Any]:
        if search:
            items = store.search_traces(query=search, limit=limit, offset=offset)
            total = store.count_search_traces(search)
        else:
            items = store.list_traces(limit=limit, offset=offset)
            total = store.count_traces()
        return {
            "items": items,
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    @app.get("/traces/compare")
    def compare_traces(baseline: str, candidate: str) -> dict[str, Any]:
        payload = _sqlite_store(store).compare_traces(baseline, candidate)
        if payload is None:
            raise HTTPException(status_code=404, detail="trace not found")
        return payload

    @app.get("/traces/{trace_id}/graph")
    def get_trace_graph(trace_id: str) -> dict[str, Any]:
        payload = _sqlite_store(store).build_causal_graph_payload(trace_id)
        if payload is None:
            raise HTTPException(status_code=404, detail="trace not found")
        return payload

    @app.get("/traces/{trace_id}/evaluation")
    def get_trace_evaluation(trace_id: str) -> dict[str, Any]:
        payload = _sqlite_store(store).build_evaluation_summary(trace_id)
        if payload is None:
            raise HTTPException(status_code=404, detail="trace not found")
        return payload

    @app.get("/traces/{trace_id}")
    def get_trace(trace_id: str) -> dict[str, Any]:
        trace = store.load_trace(trace_id)
        if trace is None:
            raise HTTPException(status_code=404, detail="trace not found")
        return trace.to_dict()

    return app


def _sqlite_store(store: Any) -> SQLiteTraceStore:
    if not isinstance(store, SQLiteTraceStore):
        raise HTTPException(status_code=501, detail="analysis endpoints require sqlite store")
    return store


app = create_app()
