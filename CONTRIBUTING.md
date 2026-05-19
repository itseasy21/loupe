# Contributing to Loupe

Thanks for helping build Loupe. The project is Python-first, local-first, and optimized for a five-minute time to first trace.

## Development Setup

```bash
python -m pip install -e '.[dev]'
python -m pytest
```

## Quality Bar

Run these before opening a pull request:

```bash
python -m ruff check .
python -m mypy loupe
python -m pytest
```

Core debugging features must stay free and local-first: recording, replay, causal tracing, CLI workflows, and local storage.
