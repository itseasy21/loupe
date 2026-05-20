# What Is Loupe?

Loupe is an open-source debugger for AI agents. It records agent runs as structured traces so developers can inspect what happened, replay important paths, and evaluate whether fixes actually improved behavior.

Traditional application logs usually tell you that something failed. Agent failures are harder: the root cause may be a bad tool result, missing context, prompt drift, unsafe output formatting, or a downstream decision that looked reasonable in isolation. Loupe gives those steps a shared trace format so they can be reviewed together.

## The Problem

Agent systems are distributed, probabilistic, and tool-heavy. A single answer may involve retrieval, planning, tool calls, model responses, retries, and validation. When the final result is wrong, teams often fall back to print statements and manual timeline reconstruction.

That workflow breaks down because:

- Raw logs rarely preserve the full input-output chain.
- Re-running the agent may not reproduce the same path.
- Tool calls, model output, and error handling are usually inspected in separate places.
- Fixes are hard to prove without replay or evaluation.

## What Loupe Captures

Loupe records each run as a trace made of spans. A span can represent a model call, tool call, retrieval step, validation step, or custom application event. Each span can include inputs, outputs, metadata, timing, and errors.

That structure lets Loupe answer questions such as:

- Which step introduced the bad context?
- Which tool call influenced the final answer?
- Did the same failure appear in a previous run?
- Did a fix improve the trace or only change the final text?

## Core Capabilities

| Capability | What it gives you |
|---|---|
| Trace recording | A local, inspectable record of agent execution |
| Deterministic replay | A way to rerun stored behavior without depending on live services |
| Causal analysis | A graph of span relationships and likely failure sources |
| Evaluation | Deterministic checks for correctness, safety, efficiency, and format |
| Local storage | SQLite-backed traces that stay on your machine by default |

## Design Principles

Loupe is built around a few constraints:

- Local-first by default, with no required cloud service.
- Framework-agnostic tracing for custom agents and common frameworks.
- CLI-first workflows that work before a dashboard is open.
- Open trace formats so captured behavior is portable.
- Small useful primitives instead of a heavyweight observability platform.

## When To Use Loupe

Use Loupe when you are building or testing an agent and need to understand behavior across multiple steps. It is especially useful for tool-using agents, multi-step workflows, regression testing, local debugging, and reproducible demos.

If you only need aggregate production metrics, a general observability tool may be enough. If you need to inspect why a specific agent run behaved the way it did, Loupe is designed for that workflow.
