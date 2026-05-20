# Loupe

Loupe is the open-source debugger for AI agents.

## What you can do today

- Record local agent runs as structured traces with spans, inputs, outputs, and errors.
- Inspect trace trees, causal graphs, replay output, and deterministic evaluations from the CLI.
- Store traces locally in SQLite and export summaries to Arrow/Parquet.
- Browse traces in the local dashboard through the FastAPI and SvelteKit apps.

## Core commands

```bash
loupe init
loupe record-demo
loupe list
loupe inspect <trace-id>
loupe graph <trace-id>
loupe replay <trace-id>
loupe evaluate <trace-id>
```

## Project references

- [What Is Loupe?](what-is-loupe.md)
- [Ideation](ideation.md)
- [Quickstart](quickstart.md)
- [How To Debug An Agent Run](how-to-debug-agent.md)
