"""Build a `RouteTree` from a nested dict, mirroring the folder layout.

    RouteTree.from_spec({
        "tickets": {
            "[ticket_id]": {
                "(detail)": {"(summary)": {}},
                "(activity)": {"inputs": ["filter"], "(comments)": {}},
            }
        }
    })

Keys that are not settings are child folders. Settings: the `RouteConfig` fields plus `layout`
(`False` = passthrough), `default` / `default_layout`, `loading`, `error` (`True` = placeholder),
`endpoint`, `inputs` (extra query inputs) and `accepts_children`. Without a `layout`, a
synthetic one renders the node id, its data, its slots and its children.
"""

from collections.abc import Mapping
from typing import Any, cast

from dash import html

from ..components import ChildContainer
from ..types import ComponentTree, Layout
from .tree import RouteConfig, RouteNode, RouteTree, classify_segment, node_id_for, passthrough_layout

_LAYOUT_FIELDS = frozenset({"default_layout", "loading", "error"})
_CONFIG_FIELDS = frozenset(RouteConfig.model_fields) - _LAYOUT_FIELDS
_SETTINGS = _CONFIG_FIELDS | _LAYOUT_FIELDS | {"layout", "default", "endpoint", "inputs", "accepts_children"}


def build_from_spec(spec: Mapping[str, Any]) -> RouteTree:
    tree = RouteTree()
    if "/" in spec:
        _add_node(tree, (), spec["/"] or {}, None)
    for key, child_spec in spec.items():
        if key != "/":
            _add_node(tree, (key,), child_spec or {}, None)
    tree.finalize()
    return tree


def _add_node(
    tree: RouteTree, rel_parts: tuple[str, ...], node_spec: Mapping[str, Any], parent: RouteNode | None
) -> None:
    kind, name = classify_segment(rel_parts[-1] if rel_parts else "/", is_root=not rel_parts)
    node_id = node_id_for(rel_parts)
    children = {k: v for k, v in node_spec.items() if k not in _SETTINGS}
    slot_names = [k[1:-1] for k in children if k.startswith("(")]
    has_child_routes = any(not k.startswith("(") for k in children)

    raw_layout: Any = node_spec.get("layout")
    synthetic = raw_layout is None or raw_layout is True
    accepts_children = node_spec.get("accepts_children", has_child_routes if synthetic else None)
    if raw_layout is False:
        layout = passthrough_layout
    elif synthetic:
        layout = _synthetic_layout(node_id, bool(accepts_children), slot_names)
    else:
        layout = cast(Layout, raw_layout)

    node = RouteNode(
        node_id=node_id,
        kind=kind,
        name=name,
        route_segments=(name,) if kind == "route" else (),
        module=f"spec.{node_id}",
        config=RouteConfig(**{k: v for k, v in node_spec.items() if k in _CONFIG_FIELDS}),
        layout=layout,
        default_layout=_placeholder(
            node_spec.get("default_layout", node_spec.get("default")),
            lambda: html.Div(f"{node_id}:default", id=f"default-{node_id}"),
        ),
        loading_layout=_placeholder(node_spec.get("loading"), lambda: html.Div(f"{node_id}:loading")),
        error_layout=_placeholder(node_spec.get("error"), lambda: _placeholder_error(node_id)),
        endpoint=node_spec.get("endpoint"),
        is_passthrough=raw_layout is False,
        explicit_inputs=frozenset(node_spec.get("inputs") or ()),
        explicit_accepts_children=accepts_children,
    )
    tree.add_node(node, parent)
    for key, child_spec in children.items():
        _add_node(tree, (*rel_parts, key), child_spec or {}, None if node.kind == "root" else node)


def _placeholder(value: Any, make: Any) -> Any:
    return make() if value is True else value


def _placeholder_error(node_id: str) -> Any:
    def error_layout(exc: BaseException, **_: Any) -> ComponentTree:
        return html.Div(f"{node_id}:error:{exc}")

    return error_layout


def _synthetic_layout(node_id: str, has_children: bool, slot_names: list[str]) -> Layout:
    def layout(children: ChildContainer | None = None, data: Any = None, **kwargs: Any) -> ComponentTree:
        parts: list[Any] = [html.Span(node_id, className="route-node-label")]
        if data is not None:
            parts.append(html.Span(str(data), className="route-node-data"))
        parts.extend(kwargs[name] for name in slot_names if kwargs.get(name) is not None)
        if has_children and children is not None:
            parts.append(children)
        return html.Div(parts, className="route-node")

    return layout
