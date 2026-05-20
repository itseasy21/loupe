# How To Debug An Agent Run

This guide walks through a local debugging loop with Loupe: record a trace, inspect it, identify likely causes, and verify the behavior after a fix.

## 1. Install Loupe

```bash
python -m pip install loupe-agent
```

The PyPI package is `loupe-agent`; the Python import package and CLI remain `loupe`.

For local development from this repository:

```bash
python -m pip install -e '.[dev]'
```

## 2. Record A Trace

Wrap the part of your agent you want to inspect:

```python
from loupe import record

with record("support-agent") as trace:
    with trace.span("tool.lookup", kind="tool", inputs={"query": "refund policy"}) as span:
        span.set_outputs({"result": "30-day refund window"})

    with trace.span("model.answer", kind="llm", inputs={"question": "Can I get a refund?"}) as span:
        span.set_outputs({"answer": "Yes, refunds are available within 30 days."})
```

Loupe stores traces locally in `.loupe/traces.db` by default.

## 3. List Recent Traces

```bash
loupe list
```

Find the trace ID for the run you want to inspect.

## 4. Inspect The Trace

```bash
loupe inspect <trace-id>
```

Look for:

- Spans with errors.
- Tool outputs that contradict the final answer.
- Missing inputs or metadata.
- Unexpected ordering or retries.
- Slow spans that may hide timeout behavior.

## 5. Generate A Causal Graph

```bash
loupe graph <trace-id>
```

The graph shows how spans relate to each other. Use it to follow the path from inputs and tool calls to downstream model decisions.

If the failure is unclear, start with the first span that contains bad data rather than the final answer. Agent failures often surface late but originate earlier.

## 6. Replay Stored Behavior

```bash
loupe replay <trace-id>
```

Replay helps separate deterministic application behavior from live service variability. If replay reproduces the issue, the trace likely contains enough evidence to debug without another live run.

## 7. Evaluate The Result

```bash
loupe evaluate <trace-id>
```

Evaluation summarizes dimensions such as correctness, safety, efficiency, and format. Treat this as debugging evidence, not a replacement for domain-specific tests.

## 8. Compare Before And After

After making a fix, record a new trace and compare the old and new runs:

```bash
loupe inspect <new-trace-id>
loupe evaluate <new-trace-id>
```

A good fix should improve the trace at the point where the failure started, not only change the final answer. Check that the new run preserves useful behavior from the old run while removing the failure path.

## Debugging Checklist

- The trace includes every important tool and model step.
- The first bad span is identified.
- The causal path from that span to the final output is understood.
- Replay behavior is checked when possible.
- Evaluation results are reviewed before and after the fix.
- The fix is captured as a test, fixture, or reproducible trace.
