from __future__ import annotations

from loupe.core.trace import SpanKind, SpanStatus
from loupe.integrations.langchain import LoupeCallbackHandler
from loupe.storage.sqlite import SQLiteTraceStore


def test_langchain_handler_records_chain_lifecycle(tmp_path) -> None:  # type: ignore[no-untyped-def]
    database = tmp_path / "langchain.db"
    handler = LoupeCallbackHandler(database=database)

    handler.on_chain_start({"name": "support-chain"}, {"input": "hello"}, "chain-1")
    handler.on_chain_end({"output": "world"}, "chain-1")

    trace = SQLiteTraceStore(database).load_trace(handler.trace.trace_id)

    assert trace is not None
    assert trace.spans[0].name == "support-chain"
    assert trace.spans[0].kind == SpanKind.AGENT
    assert trace.spans[0].inputs == {"input": "hello"}
    assert trace.spans[0].outputs == {"output": "world"}
    assert trace.spans[0].status == SpanStatus.OK


def test_langchain_handler_records_nested_llm_and_tool_spans(tmp_path) -> None:  # type: ignore[no-untyped-def]
    database = tmp_path / "nested-langchain.db"
    handler = LoupeCallbackHandler(database=database, auto_save=False)

    handler.on_chain_start({"name": "agent"}, {"input": "refund"}, "chain-1")
    handler.on_llm_start(
        {"name": "planner"}, ["plan refund lookup"], "llm-1", parent_run_id="chain-1"
    )
    handler.on_llm_end({"generations": [[{"text": "use lookup"}]]}, "llm-1")
    handler.on_tool_start(
        {"name": "lookup"}, "refund policy", "tool-1", parent_run_id="chain-1"
    )
    handler.on_tool_end("30-day refund window", "tool-1")
    handler.on_chain_end({"output": "30-day refund window"}, "chain-1")
    handler.save()

    trace = SQLiteTraceStore(database).load_trace(handler.trace.trace_id)

    assert trace is not None
    parent = trace.spans[0]
    llm = trace.spans[1]
    tool = trace.spans[2]
    assert llm.kind == SpanKind.LLM
    assert llm.parent_id == parent.span_id
    assert llm.inputs == {"prompts": ["plan refund lookup"]}
    assert tool.kind == SpanKind.TOOL
    assert tool.parent_id == parent.span_id
    assert tool.outputs == {"output": "30-day refund window"}


def test_langchain_handler_records_errors(tmp_path) -> None:  # type: ignore[no-untyped-def]
    database = tmp_path / "errors-langchain.db"
    handler = LoupeCallbackHandler(database=database)

    handler.on_tool_start({"name": "lookup"}, "refund policy", "tool-1")
    handler.on_tool_error(RuntimeError("tool failed"), "tool-1")

    trace = SQLiteTraceStore(database).load_trace(handler.trace.trace_id)

    assert trace is not None
    assert trace.spans[0].status == SpanStatus.ERROR
    assert trace.spans[0].error == "RuntimeError: tool failed"


def test_langchain_handler_stringifies_non_json_outputs(tmp_path) -> None:  # type: ignore[no-untyped-def]
    database = tmp_path / "objects-langchain.db"
    handler = LoupeCallbackHandler(database=database)

    handler.on_llm_start({"name": "planner"}, ["hello"], "llm-1")
    handler.on_llm_end(object(), "llm-1")

    trace = SQLiteTraceStore(database).load_trace(handler.trace.trace_id)

    assert trace is not None
    assert "value" in trace.spans[0].outputs
