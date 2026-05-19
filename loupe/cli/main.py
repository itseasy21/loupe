from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Annotated

import typer

from loupe import __version__
from loupe.causal.attributor import rank_failed_spans
from loupe.causal.graph import CausalGraph, build_causal_graph, export_graph
from loupe.core.trace import JsonObject, JsonValue, Span, SpanKind, SpanStatus, Trace
from loupe.eval.evaluator import DeterministicEvaluator
from loupe.replay.engine import ReplayEngine
from loupe.storage import DEFAULT_DATABASE_PATH, create_trace_store
from loupe.storage.sqlite import SQLiteTraceStore

app = typer.Typer(help="Inspect what your agent actually did.")

_MAX_CAPTURED_STREAM_CHARS = 64 * 1024


def _store(path: Path = DEFAULT_DATABASE_PATH) -> SQLiteTraceStore:
    return create_trace_store(path)


def _load_trace_or_fail(database: Path, trace_id: str) -> Trace:
    trace = _store(database).load_trace(trace_id)
    if trace is None:
        raise typer.BadParameter("trace not found")
    return trace


def _format_duration(duration_ms: float | None) -> str:
    if duration_ms is None:
        return "running"
    if duration_ms < 1000:
        return f"{duration_ms:.1f}ms"
    return f"{duration_ms / 1000:.2f}s"


def _compact_json(value: JsonValue) -> str:
    rendered = json.dumps(value, sort_keys=True)
    return rendered if len(rendered) <= 120 else f"{rendered[:117]}..."


def _captured_stream(value: str, omitted: int = 0) -> str:
    if omitted <= 0:
        return value
    return f"{value}\n... truncated {omitted} chars"


def _read_captured_file(path: Path) -> str:
    size = path.stat().st_size
    with path.open("rb") as stream:
        captured = stream.read(_MAX_CAPTURED_STREAM_CHARS)
    output = captured.decode(errors="replace")
    return _captured_stream(output, max(0, size - len(captured)))


def _run_command(command: list[str]) -> tuple[int, str, str]:
    with tempfile.NamedTemporaryFile() as stdout, tempfile.NamedTemporaryFile() as stderr:
        result = subprocess.run(
            command,
            stdout=stdout,
            stderr=stderr,
            check=False,
        )
        return (
            result.returncode,
            _read_captured_file(Path(stdout.name)),
            _read_captured_file(Path(stderr.name)),
        )


def _format_payload(label: str, payload: JsonObject) -> list[str]:
    if not payload:
        return []
    return [f"{label}: {_compact_json(payload)}"]


def _trace_status(trace: Trace) -> str:
    if any(span.status == SpanStatus.ERROR for span in trace.spans):
        return "error"
    if any(span.status == SpanStatus.UNSET for span in trace.spans):
        return "running"
    return "ok"


def _metadata_from_pairs(pairs: list[str]) -> JsonObject:
    metadata: JsonObject = {}
    for pair in pairs:
        key, separator, value = pair.partition("=")
        if not key or not separator:
            raise typer.BadParameter("metadata must use key=value format")
        metadata[key] = value
    return metadata


def _format_span(
    span: Span,
    depth: int,
    children_by_parent: dict[str | None, list[Span]],
) -> list[str]:
    indent = "  " * depth
    details = [span.kind.value, span.status.value, _format_duration(span.duration_ms)]
    lines = [f"{indent}- {span.name} ({', '.join(details)})"]
    detail_indent = "  " * (depth + 1)
    for item in [
        *_format_payload("inputs", span.inputs),
        *_format_payload("outputs", span.outputs),
    ]:
        lines.append(f"{detail_indent}{item}")
    if span.error:
        lines.append(f"{detail_indent}error: {_compact_json(span.error)}")
    for child in children_by_parent.get(span.span_id, []):
        lines.extend(_format_span(child, depth + 1, children_by_parent))
    return lines


def _inspect_trace(trace: Trace) -> str:
    status = _trace_status(trace)
    children_by_parent: dict[str | None, list[Span]] = {}
    for span in trace.spans:
        children_by_parent.setdefault(span.parent_id, []).append(span)
    lines = [
        f"Trace: {trace.name}",
        f"ID: {trace.trace_id}",
        f"Status: {status}",
        f"Started: {trace.started_at.isoformat()}",
        f"Duration: {_format_duration(trace.duration_ms)}",
        "Spans:",
    ]
    roots = children_by_parent.get(None, [])
    if not roots:
        lines.append("  (none)")
    for root in roots:
        lines.extend(_format_span(root, 1, children_by_parent))
    return "\n".join(lines)


@app.callback()
def main() -> None:
    pass


@app.command()
def version() -> None:
    typer.echo(__version__)


@app.command()
def info(
    database: Annotated[Path, typer.Option("--database", "-d")] = DEFAULT_DATABASE_PATH,
) -> None:
    store = _store(database)
    trace_count = len(store.list_traces(limit=1_000_000))
    typer.echo(f"version: {__version__}")
    typer.echo(f"default_database: {DEFAULT_DATABASE_PATH}")
    typer.echo(f"database: {database}")
    typer.echo(f"trace_count: {trace_count}")
    typer.echo("integrations: use loupe.record(...) or LoupeCallbackHandler to capture traces")


@app.command()
def init(
    database: Annotated[Path, typer.Option("--database", "-d")] = DEFAULT_DATABASE_PATH,
) -> None:
    _store(database)
    typer.echo(f"Initialized Loupe store at {database}")


@app.command(
    context_settings={
        "allow_extra_args": True,
        "ignore_unknown_options": True,
        "allow_interspersed_args": False,
    }
)
def record(
    ctx: typer.Context,
    database: Annotated[Path, typer.Option("--database", "-d")] = DEFAULT_DATABASE_PATH,
    name: Annotated[str | None, typer.Option("--name", help="Trace name")] = None,
    metadata: Annotated[
        list[str] | None,
        typer.Option("--metadata", "-m", help="Trace metadata as key=value"),
    ] = None,
) -> None:
    command = ctx.args
    if not command:
        raise typer.BadParameter("command is required")
    trace = Trace(
        name=name or Path(command[0]).name,
        metadata={"source": "loupe-cli", **_metadata_from_pairs(metadata or [])},
    )
    span = trace.add_span(
        Span(
            name="process.run",
            kind=SpanKind.AGENT,
            inputs={"command": list(command)},
        )
    )
    try:
        returncode, stdout, stderr = _run_command(list(command))
    except OSError as error:
        returncode = 127 if isinstance(error, FileNotFoundError) else 126
        stdout = ""
        stderr = f"{type(error).__name__}: {error}"
        span.finish(SpanStatus.ERROR, stderr)
    else:
        span.finish(SpanStatus.OK if returncode == 0 else SpanStatus.ERROR)
    span.set_outputs(
        {
            "returncode": returncode,
            "stdout": stdout,
            "stderr": stderr,
        }
    )
    trace.finish()
    _store(database).save_trace(trace)
    typer.echo(trace.trace_id)
    raise typer.Exit(returncode)


@app.command("record-demo")
def record_demo(
    database: Annotated[Path, typer.Option("--database", "-d")] = DEFAULT_DATABASE_PATH,
) -> None:
    trace = Trace(name="demo-agent-run", metadata={"source": "loupe-cli"})
    span = trace.add_span(
        Span(name="tool.search", kind=SpanKind.TOOL, outputs={"return_value": "found"})
    )
    span.finish()
    trace.finish()
    _store(database).save_trace(trace)
    typer.echo(trace.trace_id)


@app.command("list")
def list_command(
    database: Annotated[Path, typer.Option("--database", "-d")] = DEFAULT_DATABASE_PATH,
    limit: Annotated[int, typer.Option("--limit", "-n")] = 20,
) -> None:
    for trace in _store(database).list_traces(limit=limit):
        typer.echo(f"{trace['trace_id']}  {trace['name']}  {trace['started_at']}")


@app.command()
def show(
    trace_id: str,
    database: Annotated[Path, typer.Option("--database", "-d")] = DEFAULT_DATABASE_PATH,
) -> None:
    trace = _load_trace_or_fail(database, trace_id)
    typer.echo(json.dumps(trace.to_dict(), indent=2, sort_keys=True))


@app.command()
def inspect(
    trace_id: str,
    database: Annotated[Path, typer.Option("--database", "-d")] = DEFAULT_DATABASE_PATH,
) -> None:
    trace = _load_trace_or_fail(database, trace_id)
    typer.echo(_inspect_trace(trace))


@app.command()
def replay(
    trace_id: str,
    database: Annotated[Path, typer.Option("--database", "-d")] = DEFAULT_DATABASE_PATH,
) -> None:
    trace = _load_trace_or_fail(database, trace_id)
    outputs = [
        span.outputs.get("return_value")
        for span in trace.spans
        if span.kind == SpanKind.TOOL and "return_value" in span.outputs
    ]
    if outputs:
        for output in outputs:
            formatted = (
                json.dumps(output, sort_keys=True)
                if isinstance(output, dict | list)
                else output
            )
            typer.echo(formatted)
        return

    result = ReplayEngine().replay(trace, lambda: None)
    typer.echo(f"trace_id: {result.trace_id}")
    typer.echo(f"mocked_calls: {result.mocked_calls}")
    typer.echo("summary: no stored tool outputs to replay")


@app.command()
def evaluate(
    trace_id: str,
    database: Annotated[Path, typer.Option("--database", "-d")] = DEFAULT_DATABASE_PATH,
) -> None:
    trace = _load_trace_or_fail(database, trace_id)
    result = DeterministicEvaluator().evaluate(trace)
    typer.echo(f"score: {result.score:.2f}")
    typer.echo(f"label: {'pass' if result.passed else 'fail'}")
    typer.echo(f"reason: {result.reason}")
    for dimension, payload in result.dimensions.items():
        label = "pass" if payload.passed else "fail"
        typer.echo(
            f"dimension[{dimension}]: score={payload.score:.2f} "
            f"label={label} reason={payload.reason}"
        )


@app.command()
def search(
    query: str,
    database: Annotated[Path, typer.Option("--database", "-d")] = DEFAULT_DATABASE_PATH,
    limit: Annotated[int, typer.Option("--limit", "-n")] = 20,
) -> None:
    for trace in _store(database).search_traces(query=query, limit=limit):
        typer.echo(f"{trace['trace_id']}  {trace['name']}  {trace['started_at']}")


@app.command()
def graph(
    trace_id: str,
    database: Annotated[Path, typer.Option("--database", "-d")] = DEFAULT_DATABASE_PATH,
    output: Annotated[Path | None, typer.Option("--output", "-o")] = None,
) -> None:
    trace = _load_trace_or_fail(database, trace_id)

    causal_graph = build_causal_graph(trace)
    children_by_parent = causal_graph.edges
    roots = [span.span_id for span in trace.spans if span.parent_id is None]

    typer.echo(f"Trace {trace.trace_id} ({trace.name})")
    if not trace.spans:
        typer.echo("No spans recorded.")
        return

    for root_id in roots:
        _echo_graph_node(root_id, causal_graph, children_by_parent)

    known_parent_ids = {None, *causal_graph.nodes}
    orphan_ids = [span.span_id for span in trace.spans if span.parent_id not in known_parent_ids]
    for span_id in orphan_ids:
        _echo_graph_node(span_id, causal_graph, children_by_parent)

    scores = rank_failed_spans(trace)
    if scores:
        typer.echo("Likely causes:")
        for score in scores:
            reasons = "; ".join(score.reasons)
            typer.echo(f"- {score.span_id} {score.name} score={score.score:.3f} ({reasons})")
    if output is not None:
        written_path = export_graph(trace, causal_graph, output)
        typer.echo(f"Exported graph to {written_path}")


def _echo_graph_node(
    span_id: str,
    causal_graph: CausalGraph,
    children_by_parent: dict[str, set[str]],
    prefix: str = "",
) -> None:
    node = causal_graph.nodes[span_id]
    typer.echo(f"{prefix}- {node.span_id} {node.name} [{node.status}]")
    child_prefix = f"{prefix}  "
    for child_id in sorted(children_by_parent.get(span_id, set())):
        _echo_graph_node(child_id, causal_graph, children_by_parent, child_prefix)
