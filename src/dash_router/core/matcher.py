from collections.abc import Iterator, Mapping
from collections.abc import Set as AbstractSet
from dataclasses import dataclass, field
from typing import Any, Literal
from urllib.parse import unquote

from ..components import ChildContainer, ContainerId, RootContainer, SlotContainer, container_key
from ..types import REST_TOKENS, NodeKind, PathVariables, QueryParams, RenderMode
from .params import parse_url
from .tree import RouteNode, RouteTree

type PatchKind = Literal["root", "child", "slot"]


@dataclass(frozen=True)
class PatchTarget:
    container_id: ContainerId
    kind: PatchKind = "root"
    owner_id: str | None = None

    @staticmethod
    def root() -> "PatchTarget":
        return PatchTarget(RootContainer.ids.container, "root", None)

    @staticmethod
    def child(parent_id: str) -> "PatchTarget":
        return PatchTarget(ChildContainer.ids.container(parent_id), "child", parent_id)

    @staticmethod
    def slot(parent_id: str, slot_name: str) -> "PatchTarget":
        return PatchTarget(SlotContainer.ids.container(parent_id, slot_name), "slot", parent_id)


@dataclass(frozen=True)
class MatchedNode:
    node_id: str
    kind: NodeKind
    mode: RenderMode
    active_segment: str | None
    path_vars: PathVariables
    subscribed_query: QueryParams
    all_query: QueryParams
    child: "MatchedNode | None" = None
    slots: dict[str, "MatchedNode"] = field(default_factory=dict)
    omitted: bool = False

    @property
    def variables(self) -> dict[str, Any]:
        # Path variables take precedence over identically-named query params.
        return {**self.all_query, **self.path_vars}

    def same_render_identity(self, other: "MatchedNode") -> bool:
        return (
            self.node_id == other.node_id
            and self.mode == other.mode
            and self.omitted == other.omitted
            and self.path_vars == other.path_vars
            and self.subscribed_query == other.subscribed_query
        )

    def walk(self) -> Iterator["MatchedNode"]:
        """This node and everything below it, depth first (child before slots)."""
        yield self
        if self.child is not None:
            yield from self.child.walk()
        for slot in self.slots.values():
            yield from slot.walk()

    def find_node(self, node_id: str) -> "MatchedNode | None":
        return next((n for n in self.walk() if n.node_id == node_id), None)


@dataclass(frozen=True)
class MatchedTree:
    pathname: str
    query_params: QueryParams
    root: MatchedNode
    is_static: bool = False


@dataclass(frozen=True)
class PatchOp:
    target: PatchTarget
    subtree: MatchedNode | None  # `None` clears the container


@dataclass(frozen=True)
class TransitionPlan:
    old_url: str | None
    new_url: str
    old_tree: MatchedTree | None
    new_tree: MatchedTree | None
    patches: list[PatchOp]

    @property
    def matched(self) -> bool:
        return self.new_tree is not None

    @property
    def targets(self) -> list[ContainerId]:
        return [p.target.container_id for p in self.patches]

    def rendered_nodes(self) -> Iterator[MatchedNode]:
        for patch in self.patches:
            if patch.subtree is not None:
                yield from patch.subtree.walk()

    @property
    def segments(self) -> list[str]:
        """Node ids rendered by this transition, in render order."""
        return [n.node_id for n in self.rendered_nodes() if n.mode != "empty"]

    @property
    def modes(self) -> dict[str, RenderMode]:
        return {n.node_id: n.mode for n in self.rendered_nodes()}

    @property
    def node_vars(self) -> dict[str, dict[str, Any]]:
        return {n.node_id: n.variables for n in self.rendered_nodes() if n.mode != "empty"}


# ─── MATCHING ────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class _Matcher:
    """Matches URL segments against the tree. Every `match_*` method returns the matched node
    and whether its branch consumed the remaining segments."""

    tree: RouteTree
    query: QueryParams

    def node(
        self,
        route: RouteNode,
        mode: RenderMode,
        path_vars: PathVariables,
        active: str | None,
        child: MatchedNode | None = None,
        slots: dict[str, MatchedNode] | None = None,
        omitted: bool = False,
    ) -> MatchedNode:
        return MatchedNode(
            node_id=route.node_id,
            kind=route.kind,
            mode=mode,
            active_segment=active,
            path_vars=dict(path_vars),
            subscribed_query=route.query.normalize(self.query),
            all_query=self.query,
            child=child,
            slots=slots or {},
            omitted=omitted,
        )

    def match_branch(
        self, route: RouteNode, rem: tuple[str, ...], path_vars: PathVariables, active: str | None
    ) -> tuple[MatchedNode, bool]:
        if route.kind == "catch_all":
            return self._match_catch_all(route, rem, path_vars, active)

        if route.has_child_routes:
            child, child_valid = self.match_children(route, rem, path_vars)
        else:
            child, child_valid = None, not rem

        # A passthrough slot whose URL stops before any of its routes shows its `default.py`.
        if (
            child is None
            and child_valid
            and not rem
            and route.has_child_routes
            and route.kind == "slot"
            and route.is_passthrough
            and route.default_layout is not None
        ):
            return self.node(route, "default", path_vars, active), True

        slots, slots_consumed = self._match_slots(route, rem, path_vars)
        matched = self.node(route, "page", path_vars, active, child=child if child_valid else None, slots=slots)
        return matched, child_valid or slots_consumed

    def match_children(
        self, route: RouteNode, rem: tuple[str, ...], path_vars: PathVariables
    ) -> tuple[MatchedNode | None, bool]:
        """Priority: literal child prefix, then prefixed `[param]`, then `[param]` / `[__rest]`."""
        if not rem:
            if route.default_child:
                child_id = route.default_child_id
                if child_id is None:
                    return None, False
                child = self.tree.nodes[child_id]
                return self.match_branch(child, (), path_vars, child.name)
            if route.param_child_id is not None:
                return self._match_param(self.tree.nodes[route.param_child_id], (), path_vars)
            return None, True

        fallback: tuple[MatchedNode | None, bool] = (None, False)
        for prefix, child_id in route.child_prefixes:
            if rem[: len(prefix)] == prefix:
                result = self.match_branch(self.tree.nodes[child_id], rem[len(prefix) :], path_vars, "/".join(prefix))
                if result[1]:
                    return result
                if fallback[0] is None:
                    fallback = result
        for prefix, child_id in route.prefixed_param_children:
            if rem[: len(prefix)] == prefix:
                result = self._match_param(self.tree.nodes[child_id], rem[len(prefix) :], path_vars, prefix)
                if result[1]:
                    return result
                if fallback[0] is None:
                    fallback = result
        if route.param_child_id is not None:
            result = self._match_param(self.tree.nodes[route.param_child_id], rem, path_vars)
            if result[1]:
                return result
            if fallback[0] is None:
                fallback = result
        return fallback

    def _match_param(
        self,
        route: RouteNode,
        rem: tuple[str, ...],
        path_vars: PathVariables,
        prefix: tuple[str, ...] = (),
    ) -> tuple[MatchedNode, bool]:
        if route.kind == "catch_all":
            return self.match_branch(route, rem, path_vars, "/".join((*prefix, *rem)) or None)
        if not rem:
            # Omitted placeholder, e.g. `/tickets` matching `tickets/[ticket_id]` with `ticket_id=None`.
            mode: RenderMode = "default" if route.default_layout is not None else "page"
            omitted_vars = {**path_vars, route.name: None}
            return self.node(route, mode, omitted_vars, None, omitted=True), True
        return self.match_branch(route, rem[1:], {**path_vars, route.name: rem[0]}, rem[0])

    def _match_catch_all(
        self, route: RouteNode, rem: tuple[str, ...], path_vars: PathVariables, active: str | None
    ) -> tuple[MatchedNode, bool]:
        path_vars = {**path_vars, "rest": list(rem)}
        if not rem and route.default_layout is not None:
            return self.node(route, "default", path_vars, active), True
        slots = {
            name: self.match_branch(self.tree.nodes[slot_id], (), path_vars, name)[0]
            for name, slot_id in route.slots.items()
        }
        return self.node(route, "page", path_vars, active, slots=slots), True

    def _match_slots(
        self, route: RouteNode, rem: tuple[str, ...], path_vars: PathVariables
    ) -> tuple[dict[str, MatchedNode], bool]:
        """Each slot gets its own cursor. Returns `(slots, any_consumed_rem)`."""
        slots: dict[str, MatchedNode] = {}
        consumed = False
        for name, slot_id in route.slots.items():
            slot = self.tree.nodes[slot_id]
            if not self.tree.slot_has_route_branches(slot_id):
                # Passive slot: scoped to the parent's path variables only.
                slots[name] = self.match_branch(slot, (), path_vars, name)[0]
                continue
            matched, valid = self.match_branch(slot, rem, path_vars, name)
            if valid:
                slots[name] = matched
                consumed = consumed or bool(rem)
            else:
                slots[name] = self._unmatched_slot(slot, path_vars, name)
        return slots, consumed

    def _unmatched_slot(self, slot: RouteNode, path_vars: PathVariables, name: str) -> MatchedNode:
        """A parallel slot that does not match the URL shows `default.py`, or renders empty."""
        mode: RenderMode = "default" if slot.default_layout is not None else "empty"
        return self.node(slot, mode, path_vars, name)


def _static_specificity(node: RouteNode) -> tuple[int, int, int]:
    if node.node_id == "/":
        return (3, 0, 0)
    parts = [p for p in node.node_id.split("/") if p]
    params = [p[1:-1] for p in parts if p.startswith("[") and p.endswith("]")]
    has_catch_all = any(p in REST_TOKENS for p in params)
    return (0 if has_catch_all else 1, len(parts) - len(params), len(parts))


def _match_static_path(node: RouteNode, segments: tuple[str, ...]) -> PathVariables | None:
    pattern = tuple(p for p in node.node_id.split("/") if p) if node.node_id != "/" else ()
    path_vars: PathVariables = {}
    for idx, part in enumerate(pattern):
        if part.startswith("[") and part.endswith("]"):
            inner = part[1:-1]
            if inner in REST_TOKENS:
                path_vars["rest"] = list(segments[idx:])
                return path_vars
            if idx >= len(segments):
                return None
            path_vars[inner.replace("-", "_")] = segments[idx]
        elif idx >= len(segments) or segments[idx] != part:
            return None
    return path_vars if len(segments) == len(pattern) else None


def match_url(
    tree: RouteTree,
    url: str,
    extra_inputs: Mapping[str, Any] | None = None,
) -> MatchedTree | None:
    pathname, query = parse_url(url)
    query = {**query, **(extra_inputs or {})}
    segments = tuple(unquote(seg) for seg in pathname.split("/") if seg)
    matcher = _Matcher(tree, query)

    # Standalone `is_static=True` routes win, most specific first.
    for node in sorted(tree.static_nodes, key=_static_specificity, reverse=True):
        static_vars = _match_static_path(node, segments)
        if static_vars is not None:
            return MatchedTree(pathname, query, matcher.node(node, "page", static_vars, pathname), is_static=True)

    if tree.root_shell_id is not None:
        root, valid = matcher.match_branch(tree.nodes[tree.root_shell_id], segments, {}, "/")
    elif segments:
        root, valid = matcher.match_children(tree.root_virtual, segments, {})
    else:
        return None
    return MatchedTree(pathname, query, root) if valid and root is not None else None


# ─── DIFFING ─────────────────────────────────────────────────────────────────


def plan_transition(
    tree: RouteTree,
    old_url: str | None,
    new_url: str,
    extra_inputs: Mapping[str, Any] | None = None,
    prev_extra_inputs: Mapping[str, Any] | None = None,
) -> TransitionPlan:
    """Diff `old_url` against `new_url` and return the minimal container patches."""
    old_tree = (
        match_url(tree, old_url, prev_extra_inputs if prev_extra_inputs is not None else extra_inputs)
        if old_url is not None
        else None
    )
    new_tree = match_url(tree, new_url, extra_inputs)
    patches = _diff_trees(old_tree, new_tree)
    return TransitionPlan(old_url, new_url, old_tree, new_tree, patches)


def _unchanged(old: MatchedNode, new: MatchedNode) -> bool:
    return old.same_render_identity(new)


def _diff_trees(old: MatchedTree | None, new: MatchedTree | None) -> list[PatchOp]:
    if new is None:
        return [PatchOp(PatchTarget.root(), None)]
    if old is None or old.is_static or new.is_static or not _unchanged(old.root, new.root):
        return [PatchOp(PatchTarget.root(), new.root)]
    patches: list[PatchOp] = []
    _diff_nodes(old.root, new.root, patches)
    return patches


def _diff_nodes(old: MatchedNode, new: MatchedNode, patches: list[PatchOp]) -> None:
    """Walk two nodes with the same render identity and emit the minimal container patches."""
    if old.child is not None and new.child is not None and _unchanged(old.child, new.child):
        _diff_nodes(old.child, new.child, patches)
    elif old.child is not None or new.child is not None:
        patches.append(PatchOp(PatchTarget.child(new.node_id), new.child))

    for slot_name, new_slot in new.slots.items():
        old_slot = old.slots.get(slot_name)
        if old_slot is not None and _unchanged(old_slot, new_slot):
            _diff_nodes(old_slot, new_slot, patches)
        else:
            patches.append(PatchOp(PatchTarget.slot(new.node_id, slot_name), new_slot))


def resolve_targets(plan: TransitionPlan, existing_keys: AbstractSet[str]) -> list[PatchOp]:
    """Lift any patch whose container is not mounted yet to its nearest existing ancestor.

    When a parent boundary is still showing its loading skeleton (or omitted its child container),
    a child patch would target a non-existent container. Walking up replaces the ancestor
    instead, and any patch inside that ancestor's subtree is dropped.
    """
    if not plan.matched or plan.new_tree is None:
        return list(plan.patches)

    placements: dict[str, tuple[PatchTarget, MatchedNode]] = {}

    def record(node: MatchedNode, target: PatchTarget) -> None:
        placements[node.node_id] = (target, node)
        if node.child is not None:
            record(node.child, PatchTarget.child(node.node_id))
        for slot_name, slot in node.slots.items():
            record(slot, PatchTarget.slot(node.node_id, slot_name))

    record(plan.new_tree.root, PatchTarget.root())

    lifted: list[PatchOp] = []
    seen: set[str] = set()
    for patch in plan.patches:
        target = patch.target
        subtree = patch.subtree
        while container_key(target.container_id) not in existing_keys:
            if target.owner_id is None:
                break
            placement = placements.get(target.owner_id)
            if placement is None:
                break
            target, subtree = placement
        key = container_key(target.container_id)
        if key not in seen:
            seen.add(key)
            lifted.append(PatchOp(target, subtree))

    covered_owners = {n.node_id for p in lifted if p.subtree is not None for n in p.subtree.walk()}
    return [p for p in lifted if p.target.owner_id is None or p.target.owner_id not in covered_owners]
