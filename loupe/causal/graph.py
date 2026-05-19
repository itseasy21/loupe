from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from loupe.core.trace import Trace


@dataclass(frozen=True, slots=True)
class CausalNode:
    span_id: str
    parent_id: str | None
    name: str
    status: str


@dataclass(slots=True)
class CausalGraph:
    nodes: dict[str, CausalNode] = field(default_factory=dict)
    edges: dict[str, set[str]] = field(default_factory=dict)

    def parents_of(self, span_id: str) -> set[str]:
        return {parent for parent, children in self.edges.items() if span_id in children}


def build_causal_graph(trace: Trace) -> CausalGraph:
    graph = CausalGraph()
    for span in trace.spans:
        graph.nodes[span.span_id] = CausalNode(
            span_id=span.span_id,
            parent_id=span.parent_id,
            name=span.name,
            status=span.status.value,
        )
        if span.parent_id is not None:
            graph.edges.setdefault(span.parent_id, set()).add(span.span_id)
    return graph


def render_graph_svg(trace: Trace, graph: CausalGraph) -> str:
    nodes = list(trace.spans)
    width = 960
    row_height = 84
    padding = 32
    radius = 16
    height = max(160, padding * 2 + row_height * max(1, len(nodes)))
    card_width = width - padding * 2
    circle_x = padding + 32
    text_x = padding + 72
    line_x = circle_x
    lines = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
            f'height="{height}" viewBox="0 0 {width} {height}" role="img" '
            'aria-labelledby="title desc">'
        ),
        '<title id="title">Loupe causal graph</title>',
        (
            f'<desc id="desc">Trace {trace.trace_id} causal graph for '
            f'{trace.name}</desc>'
        ),
        '<rect width="100%" height="100%" fill="#f7f4ed" />',
        (
            f'<text x="{padding}" y="28" font-size="20" '
            'font-family="monospace" fill="#1f2933">'
            f'Trace {trace.name}</text>'
        ),
    ]
    if nodes:
        first_y = padding + 28
        last_y = padding + 28 + row_height * (len(nodes) - 1)
        lines.append(
            f'<line x1="{line_x}" y1="{first_y}" x2="{line_x}" '
            f'y2="{last_y}" stroke="#cbd5e1" stroke-width="4" '
            'stroke-linecap="round" />'
        )
    for index, span in enumerate(nodes):
        y = padding + 28 + row_height * index
        color = _status_color(graph.nodes[span.span_id].status)
        lines.extend(
            [
                (
                    f'<rect x="{padding}" y="{y - 24}" width="{card_width}" '
                    f'height="52" rx="{radius}" fill="#fffdf8" '
                    'stroke="#d7d2c7" />'
                ),
                (
                    f'<circle cx="{circle_x}" cy="{y}" r="13" fill="{color}" '
                    'stroke="#ffffff" stroke-width="3" />'
                ),
                (
                    f'<text x="{text_x}" y="{y - 4}" font-size="15" '
                    'font-family="monospace" fill="#111827">'
                    f'{_xml_escape(span.name)}</text>'
                ),
                (
                    f'<text x="{text_x}" y="{y + 16}" font-size="12" '
                    'font-family="monospace" fill="#475569">'
                    f'{_node_detail(graph.nodes[span.span_id])}</text>'
                ),
            ]
        )
    lines.append('</svg>')
    return ''.join(lines)


def export_graph(trace: Trace, graph: CausalGraph, output_path: Path) -> Path:
    suffix = output_path.suffix.lower()
    svg = render_graph_svg(trace, graph)
    if suffix == '.svg':
        output_path.write_text(svg, encoding='utf-8')
        return output_path
    if suffix == '.png':
        output_path.write_text(svg, encoding='utf-8')
        return output_path
    raise ValueError('output path must end with .svg or .png')


def _node_detail(node: CausalNode) -> str:
    parent = node.parent_id or 'root'
    return f'{node.status} | parent={parent}'


def _status_color(status: str) -> str:
    if status == 'error':
        return '#c2410c'
    if status == 'ok':
        return '#15803d'
    return '#475569'


def _xml_escape(value: str) -> str:
    return (
        value.replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
        .replace('"', '&quot;')
        .replace("'", '&apos;')
    )
