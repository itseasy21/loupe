# Quickstart

Install Loupe:

```bash
pip install loupe-agent
```

The PyPI package is `loupe-agent`; the Python import and CLI remain `loupe`.

Record a trace:

```python
from loupe import record

with record("support-agent") as trace, trace.span(
    "tool.lookup", kind="tool", inputs={"query": "refund policy"}
) as span:
    span.set_outputs({"result": "30-day refund window"})
```

Inspect the saved trace:

```bash
loupe list
loupe inspect <trace-id>
```

The default local database path is `.loupe/traces.db`.
