# Loupe

[![CI](https://github.com/loupe/loupe/actions/workflows/ci.yml/badge.svg)](https://github.com/loupe/loupe/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/loupe.svg)](https://pypi.org/project/loupe/)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Stars](https://img.shields.io/github/stars/loupe/loupe?style=social)](https://github.com/loupe/loupe)

Loupe is the open-source debugger for AI agents.

> Inspect what your agent actually did.

## Quick Start

```bash
pip install loupe
```

```python
from loupe import record

with record("support-agent") as trace, trace.span(
    "tool.lookup", kind="tool", inputs={"query": "refund policy"}
) as span:
    span.set_outputs({"result": "30-day refund window"})
```

Loupe writes traces to `.loupe/traces.db` by default, so you can inspect the run locally:

```bash
loupe list
loupe inspect <trace-id>
```

Or create a local demo trace from the CLI:

```bash
loupe init
loupe record-demo
loupe list
```

## Features

- Record agent runs as structured traces with spans, events, inputs, outputs, and errors.
- Replay deterministic tool calls locally using stored outputs and mock patches.
- Build causal graphs that show which span influenced downstream behavior.
- Export causal graphs as SVG assets, or write SVG content to a requested `.png` path when no raster renderer is installed.
- Rank likely failure causes with deterministic blame scoring.
- Store traces locally in SQLite and export summaries to Arrow/Parquet.
- Serve traces over a FastAPI API for future SvelteKit dashboard integration.

## Framework Support

| Framework | Status | Integration Path |
|---|---:|---|
| LangChain | Scaffolded | Callback handler |
| CrewAI | Planned | Event listener adapter |
| AutoGen / AG2 | Planned | Message hook interceptor |
| LangGraph | Planned | Node middleware |
| Raw OpenTelemetry | Planned | Span exporter bridge |

## Project Links

- Documentation site: run `mkdocs serve` locally or `mkdocs build` for a static site build
- Documentation source: `docs/`
- Contributing: `CONTRIBUTING.md`
- Security policy: `SECURITY.md`
- Community Discord: coming soon
- GitHub Discussions: coming soon

## Development

```bash
python -m pip install -e '.[dev]'
python -m ruff check .
python -m mypy loupe
python -m pytest
```
