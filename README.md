# Loupe — Open-Source Debugger for AI Agents

[![CI](https://github.com/itseasy21/loupe/actions/workflows/ci.yml/badge.svg)](https://github.com/itseasy21/loupe/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/loupe-agent.svg)](https://pypi.org/project/loupe-agent/)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](pyproject.toml)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=brightgreen)](.pre-commit-config.yaml)

> **Inspect what your agent actually did. Find out why it failed. Prove the fix works.**

Loupe is a local-first, open-source debugging platform for AI agents — built for developers who ship agents in production and need to understand, replay, and verify agent behavior the way `rr` works for C programs or Chrome DevTools works for web apps.

---

## Why Loupe?

AI agents fail in ways traditional software doesn't. The root cause is rarely the model — it's the system around it: bad tool inputs, unexpected state, missed edge cases, cascading errors across multi-step reasoning. Existing tools give you logs. Loupe gives you **causality**.

- **88%** of agent failures are caused by the system, not the model.
- Teams spend **40% of sprint time** investigating agent failures.
- **Zero** open-source tools combine recording, replay, causal tracing, and CI verification in one platform.

Loupe changes that.

---

## Quick Start

### Install

```bash
pip install loupe-agent
```

The PyPI package is `loupe-agent`; the Python import package and CLI remain `loupe`.

### Record an agent run

```python
from loupe import record

with record("support-agent") as trace, trace.span(
    "tool.lookup", kind="tool", inputs={"query": "refund policy"}
) as span:
    span.set_outputs({"result": "30-day refund window"})
```

Traces are written to `.loupe/traces.db` automatically.

### Inspect from the CLI

```bash
loupe list                              # list all recorded traces
loupe inspect <trace-id>                # inspect span tree, inputs, outputs, errors
loupe graph <trace-id>                   # render causal graph as SVG
loupe evaluate <trace-id>               # run deterministic evaluation
```

### Or create a demo trace to explore

```bash
loupe init
loupe record-demo
loupe list
```

---

## Core Features

### 📼 Structured Recording
Drop-in SDK captures every agent step: spans, events, inputs, outputs, errors, latency, and token counts. Zero code changes for LangChain integrations.

### 🔄 Deterministic Replay
Record once, replay infinitely. Stored outputs and mock patches ensure byte-identical results every time — no more "works on my machine" failures.

### 🔍 Causal Tracing
Automatic dependency graphs show which span influenced downstream behavior. Blame assignment ranks likely failure causes: bad input, wrong tool, bad prompt, or model hallucination.

### ✅ CI/CD Verification
Deterministic evaluation gates catch agent behavior regressions before they ship. Run evaluations in your existing CI pipeline.

### 🏗️ Local-First Storage
SQLite storage by default — your traces never leave your machine. Export summaries to Arrow/Parquet for downstream analysis.

### 🌐 API for Dashboards
Serve traces over FastAPI for integration with web-based trace explorers and dashboards.

---

## Architecture

```
Agent Code
    │
    ▼
┌─────────────────┐     ┌──────────────────┐
│  Loupe SDK      │────▶│  .loupe/traces.db │
│  (record spans) │     │  (SQLite)          │
└─────────────────┘     └────────┬───────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
              loupe inspect  loupe graph  loupe evaluate
              (CLI detail)   (causal DAG)  (deterministic eval)
                    │            │            │
                    └────────────┴────────────┘
                              │
                     FastAPI Server (optional)
                              │
                    SvelteKit Dashboard (optional)
```

---

## Framework Support

| Framework | Status | Integration |
|---|---|---|
| LangChain | Scaffolded | Callback handler |
| CrewAI | Planned | Event listener adapter |
| AutoGen / AG2 | Planned | Message hook interceptor |
| LangGraph | Planned | Node middleware |
| Raw OpenTelemetry | Planned | Span exporter bridge |

---

## Development Setup

```bash
# Clone and install
git clone https://github.com/itseasy21/loupe.git
cd loupe
python -m pip install -e '.[dev]'

# Run quality checks
python -m ruff check .
python -m mypy loupe
python -m pytest

# Or use pre-commit hooks (recommended)
python -m pip install pre-commit
python -m pre-commit install
python -m pre-commit run --all-files
```

### Running the Dashboard

```bash
# Start the API server
cd loupe && uvicorn loupe.api.server:app --reload --port 8000

# In another terminal, start the frontend
cd frontend && npm install && npm run dev
```

---

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions, coding standards, and the PR process.

- **Bugs & issues**: https://github.com/itseasy21/loupe/issues
- **Discussions**: https://github.com/itseasy21/loupe/discussions

---

## License

Loupe is open-source under the [Apache 2.0 License](LICENSE).
