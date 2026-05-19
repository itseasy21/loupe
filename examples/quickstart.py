from loupe import record

with record("support-agent") as trace, trace.span(
    "tool.lookup", kind="tool", inputs={"query": "refund policy"}
) as span:
    span.set_outputs({"result": "30-day refund window"})

print(f"Recorded trace {trace.trace_id} in .loupe/traces.db")
