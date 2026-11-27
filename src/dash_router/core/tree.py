from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

from ..components import ChildContainer
from ..errors import RouteTreeValidationError
from ..types import REST_TOKENS, ComponentTree, Endpoint, ErrorLayout, Layout, NodeKind
from .params import FunctionSignatureInfo, as_list


class RouteConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)

    default_child: str | None = None
    is_static: bool = False
    title: str | Callable[..., str] | None = None
    description: str | None = None
    name: str | None = None
    order: int | None = None
    image: str | None = None
    image_url: str | None = None
    redirect_from: list[str] | None = None
    default_layout: Layout | None = Field(default=None, alias="default")
    loading: Layout | None = None
    error: ErrorLayout | None = None
    meta: dict[str, Any] = Field(default_factory=dict)


def url_segment(name: str) -> str:
    """Folder name -> URL segment (`order_items` / `order items` -> `order-items`)."""
    return name.replace("_", "-").replace(" ", "-")


def classify_segment(raw_segment: str, is_root: bool = False) -> tuple[NodeKind, str]:
    if is_root or raw_segment == "/":
        return "root", "/"
    if raw_segment.startswith("(") and raw_segment.endswith(")"):
        return "slot", raw_segment[1:-1]
    if raw_segment.startswith("[") and raw_segment.endswith("]"):
        inner = raw_segment[1:-1]
        return ("catch_all", "rest") if inner in REST_TOKENS else ("param", inner.replace("-", "_"))
    return "route", url_segment(raw_segment)


def node_id_for(rel_parts: tuple[str, ...]) -> str:
    if not rel_parts:
        return "/"
    return "/".join(p if p.startswith(("(", "[")) else url_segment(p) for p in rel_parts)


def passthrough_layout(children: ChildContainer | None = None, **_: Any) -> ComponentTree:
    return children


@dataclass(frozen=True)
class QueryInputs:
    """Query parameters a node subscribes to, with their declared defaults and coercion."""

    names: frozenset[str] = frozenset()
    defaults: dict[str, Any] = field(default_factory=dict)
    adapters: dict[str, TypeAdapter[Any]] = field(default_factory=dict)
    collections: frozenset[str] = frozenset()

    @classmethod
    def from_signatures(cls, *sigs: FunctionSignatureInfo, extra: frozenset[str] = frozenset()) -> "QueryInputs":
        return cls(
            names=frozenset().union(extra, *(s.query_inputs for s in sigs)),
            defaults={k: v for s in sigs for k, v in s.input_defaults.items()},
            adapters={k: v for s in sigs for k, v in s.type_adapters.items()},
            collections=frozenset().union(*(s.collection_inputs for s in sigs)),
        )

    def normalize(self, query: Mapping[str, Any]) -> dict[str, Any]:
        """Subscribed values in canonical form, so `?page=1` and an omitted `page` (default 1)
        compare equal."""
        out: dict[str, Any] = {}
        for key in self.names:
            raw = query.get(key)
            if raw is None:
                if key in self.defaults:
                    out[key] = self.defaults[key]
                continue
            if key in self.collections:
                raw = as_list(raw)
            adapter = self.adapters.get(key)
            try:
                out[key] = adapter.validate_python(raw) if adapter is not None else raw
            except Exception:
                out[key] = raw
        return out


@dataclass
class RouteNode:
    node_id: str
    kind: NodeKind
    name: str  # slot name, param name, URL segment, or "/"
    route_segments: tuple[str, ...] = ()  # URL segment(s) matched at the parent for "route" nodes
    module: str = ""
    config: RouteConfig = field(default_factory=RouteConfig)
    parent_id: str | None = None

    layout: Layout = passthrough_layout
    default_layout: Layout | None = None
    loading_layout: Layout | None = None
    error_layout: ErrorLayout | None = None
    endpoint: Endpoint | None = None
    is_passthrough: bool = False
    # Spec-only overrides of what the layout signature declares.
    explicit_inputs: frozenset[str] = frozenset()
    explicit_accepts_children: bool | None = None

    children: dict[str, str] = field(default_factory=dict)  # joined route segments -> node_id
    child_prefixes: list[tuple[tuple[str, ...], str]] = field(default_factory=list)
    prefixed_param_children: list[tuple[tuple[str, ...], str]] = field(default_factory=list)
    param_child_id: str | None = None
    slots: dict[str, str] = field(default_factory=dict)  # slot_name -> node_id
    children_warned: bool = False

    layout_sig: FunctionSignatureInfo = field(default_factory=FunctionSignatureInfo)
    default_sig: FunctionSignatureInfo = field(default_factory=FunctionSignatureInfo)
    loading_sig: FunctionSignatureInfo = field(default_factory=FunctionSignatureInfo)
    error_sig: FunctionSignatureInfo = field(default_factory=FunctionSignatureInfo)
    endpoint_sig: FunctionSignatureInfo = field(default_factory=FunctionSignatureInfo)
    title_sig: FunctionSignatureInfo = field(default_factory=FunctionSignatureInfo)
    query: QueryInputs = field(default_factory=QueryInputs)
    accepts_children: bool = False

    @property
    def is_static(self) -> bool:
        return self.config.is_static

    @property
    def default_child(self) -> str | None:
        return self.config.default_child

    @property
    def default_child_id(self) -> str | None:
        if not self.default_child:
            return None
        return self.children.get(url_segment(self.default_child)) or self.children.get(self.default_child)

    @property
    def is_path_template(self) -> bool:
        return self.kind in ("param", "catch_all")

    @property
    def has_child_routes(self) -> bool:
        return bool(self.child_prefixes or self.prefixed_param_children or self.param_child_id)

    def analyze_signatures(self) -> None:
        slot_names = set(self.slots)
        self.layout_sig = FunctionSignatureInfo.analyze(self.layout, slot_names)
        self.default_sig = FunctionSignatureInfo.analyze(self.default_layout, slot_names)
        self.loading_sig = FunctionSignatureInfo.analyze(self.loading_layout, slot_names)
        self.error_sig = FunctionSignatureInfo.analyze(self.error_layout, slot_names)
        self.endpoint_sig = FunctionSignatureInfo.analyze(self.endpoint, slot_names)
        self.title_sig = (
            FunctionSignatureInfo.analyze(self.config.title, slot_names)
            if callable(self.config.title)
            else FunctionSignatureInfo()
        )
        # A path template's own parameter is a path variable, not a query input.
        own_param = frozenset({self.name}) if self.is_path_template else frozenset()
        query = QueryInputs.from_signatures(self.layout_sig, self.endpoint_sig, extra=self.explicit_inputs)
        self.query = QueryInputs(query.names - own_param, query.defaults, query.adapters, query.collections)
        self.accepts_children = (
            self.explicit_accepts_children
            if self.explicit_accepts_children is not None
            else self.layout_sig.accepts_children
        )

    def register_child(self, child: "RouteNode") -> None:
        child.parent_id = None if self.node_id == _VIRTUAL_ROOT_ID else self.node_id
        if child.kind == "slot":
            if child.name in self.slots:
                raise KeyError(f"Slot '{child.name}' is already registered on '{self.node_id}'.")
            self.slots[child.name] = child.node_id
        elif child.is_path_template and child.route_segments:
            self.prefixed_param_children.append((child.route_segments, child.node_id))
            self.prefixed_param_children.sort(key=lambda item: len(item[0]), reverse=True)
        elif child.is_path_template:
            if self.param_child_id is not None:
                raise ValueError(
                    f"Node '{self.node_id}' already defines dynamic child '{self.param_child_id}'; "
                    f"cannot also register '{child.node_id}'."
                )
            self.param_child_id = child.node_id
        else:
            key = "/".join(child.route_segments)
            if key in self.children:
                raise KeyError(f"Child route '{key}' is already registered on '{self.node_id}'.")
            self.children[key] = child.node_id
            self.child_prefixes.append((child.route_segments, child.node_id))
            # Longest prefix first so multi-segment routes match before shorter ones.
            self.child_prefixes.sort(key=lambda item: len(item[0]), reverse=True)


_VIRTUAL_ROOT_ID = "__root__"


def _virtual_root() -> RouteNode:
    return RouteNode(node_id=_VIRTUAL_ROOT_ID, kind="root", name="/", module=_VIRTUAL_ROOT_ID, is_passthrough=True)


class RouteTree:
    """Instance-scoped routing tree.

    Top-level routes hang off `root_virtual` until `finalize()` decides whether `pages/page.py`
    is a persistent shell (it renders `children` or has slots) that adopts them, or a standalone
    static index page.
    """

    def __init__(self, default_error_layout: ErrorLayout | None = None) -> None:
        self.nodes: dict[str, RouteNode] = {}
        self.static_nodes: list[RouteNode] = []
        self.root_shell_id: str | None = None
        self.root_virtual: RouteNode = _virtual_root()
        self.default_error_layout: ErrorLayout | None = default_error_layout
        self.default_error_sig: FunctionSignatureInfo = FunctionSignatureInfo.analyze(default_error_layout)
        self._route_branches: dict[str, bool] = {}

    @classmethod
    def from_folder(
        cls,
        pages_folder: str | Path,
        ignore_empty_folders: bool = False,
        default_error_layout: ErrorLayout | None = None,
        package_prefix: str = "pages",
    ) -> "RouteTree":
        from .loader import load_folder

        return load_folder(pages_folder, ignore_empty_folders, default_error_layout, package_prefix)

    @classmethod
    def from_spec(cls, spec: Mapping[str, Any]) -> "RouteTree":
        """Build a tree from a nested dict (see `core/spec.py`); handy for tests."""
        from .spec import build_from_spec

        return build_from_spec(spec)

    def add_node(self, node: RouteNode, parent: RouteNode | None) -> None:
        if node.node_id in self.nodes:
            raise KeyError(f"Route node '{node.node_id}' is already registered.")
        self.nodes[node.node_id] = node
        if node.kind == "root":
            return
        if node.is_static:
            self.static_nodes.append(node)
            return
        (parent or self.root_virtual).register_child(node)

    def finalize(self) -> None:
        for node in self.nodes.values():
            node.analyze_signatures()
        root = self.nodes.get("/")
        if root is not None:
            if not root.is_static and (root.accepts_children or root.slots):
                self._promote_root_shell(root)
            else:
                root.config = root.config.model_copy(update={"is_static": True})
                if root not in self.static_nodes:
                    self.static_nodes.append(root)
        self._route_branches.clear()
        for node in self.nodes.values():
            _validate(node)

    def _promote_root_shell(self, root: RouteNode) -> None:
        vroot = self.root_virtual
        top_level = [
            *(cid for _, cid in vroot.child_prefixes),
            *(cid for _, cid in vroot.prefixed_param_children),
            *([vroot.param_child_id] if vroot.param_child_id else []),
            *vroot.slots.values(),
        ]
        for child_id in top_level:
            root.register_child(self.nodes[child_id])
        self.root_virtual = _virtual_root()
        self.root_shell_id = root.node_id
        root.analyze_signatures()

    def slot_has_route_branches(self, slot_node_id: str) -> bool:
        """True if the slot (or a slot nested in it) defines child or `[param]` routes."""
        cached = self._route_branches.get(slot_node_id)
        if cached is None:
            node = self.nodes[slot_node_id]
            cached = node.has_child_routes or any(self.slot_has_route_branches(s) for s in node.slots.values())
            self._route_branches[slot_node_id] = cached
        return cached


def _validate(node: RouteNode) -> None:
    has_routes = bool(node.children or node.param_child_id)
    if node.is_static and node.kind != "root" and (has_routes or node.slots):
        raise RouteTreeValidationError(
            f"Route node '{node.node_id}' is marked as static but has child routes or slots. "
            "Either remove is_static=True or remove them."
        )
    if node.kind == "catch_all" and has_routes:
        raise RouteTreeValidationError(
            f"Catch-all node '{node.node_id}' must be a leaf in its route branch "
            "(slots are allowed, child routes are not)."
        )
    if node.default_child and node.default_child_id is None:
        raise RouteTreeValidationError(
            f"Route node '{node.node_id}' sets default_child='{node.default_child}', "
            f"but no matching child route exists in {sorted(node.children)}."
        )
