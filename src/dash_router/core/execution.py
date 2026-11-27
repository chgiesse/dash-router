"""Render a `TransitionPlan` or an individual `LazyContainer` subtree.

During navigation (`render_patches`), `loading.py` boundaries and streaming (generator)
layouts are wrapped in a `LazyContainer` carrying its fallback and planned route. Each
`LazyContainer` then loads its subtree (and streams generator updates) through its own
Dash `MATCH` streaming callback (`render_lazy`).
"""

import asyncio
import inspect
import logging
from collections.abc import AsyncGenerator, Awaitable, Iterable, Iterator, Mapping
from contextlib import suppress
from dataclasses import dataclass
from typing import Any

from dash import html, no_update
from dash.development.base_component import Component

from .._url_for import build_route_path
from ..components import ChildContainer, ContainerId, LazyContainer, SlotContainer
from ..types import ComponentTree, ErrorLayout
from .matcher import MatchedNode, PatchOp, TransitionPlan, match_url
from .params import FunctionSignatureInfo, invoke, start_callable
from .tree import RouteNode, RouteTree

_GEN_DONE = object()
logger = logging.getLogger("dash_router")


@dataclass(frozen=True)
class PatchUpdate:
    container_id: ContainerId
    children: ComponentTree


# ─── RENDERING ───────────────────────────────────────────────────────────────


@dataclass
class _Renderer:
    """One render pass over matched subtrees.

    With `lazy_boundaries=False` everything renders eagerly. With `lazy_boundaries=True`,
    `loading.py` boundaries and generator layouts (other than `skip_defer_node`) render
    as `LazyContainer` shells whose content loads via `render_lazy`.
    """

    tree: RouteTree
    endpoint_results: dict[str, Any]
    nav_seq: int = 0
    url: str = ""
    extra_inputs: Mapping[str, Any] | None = None
    lazy_boundaries: bool = False
    skip_defer_node: str | None = None
    path_prefix: str = "/"

    def base_href(self, matched: MatchedNode) -> str | None:
        """Browser path of `matched` (with the app's pathname prefix), without a trailing slash."""
        try:
            path = build_route_path(matched.node_id, matched.path_vars)
        except (ValueError, TypeError):
            return None
        return (self.path_prefix.rstrip("/") + path).rstrip("/")

    async def render_patch(self, patch: PatchOp) -> PatchUpdate:
        cid = patch.target.container_id
        if patch.subtree is None:
            return PatchUpdate(cid, None)
        return PatchUpdate(cid, await self.render(patch.subtree))

    async def render(self, matched: MatchedNode) -> ComponentTree:
        if matched.mode == "empty":
            return None
        node = self.tree.nodes[matched.node_id]
        variables = matched.variables
        if matched.mode == "default":
            if node.default_layout is not None:
                return await _invoke_or_error(self.tree, node, node.default_layout, node.default_sig, variables)
            return await _invoke_or_error(self.tree, node, node.layout, node.layout_sig, variables)
        if self.lazy_boundaries and matched.node_id != self.skip_defer_node and _is_lazy_boundary(node, matched):
            return await self._defer(node, matched)

        data = self.endpoint_results.get(node.node_id)
        if isinstance(data, BaseException):
            return await render_error(self.tree, node, data, variables)
        injected = {**await self._render_containers(node, matched), "data": data}
        return await _invoke_layout(self.tree, node, matched, injected)

    async def _render_containers(self, node: RouteNode, matched: MatchedNode) -> dict[str, Any]:
        """Render the child and slot containers handed to `node`'s layout, concurrently."""
        base = self.base_href(matched)

        async def child() -> ChildContainer:
            if matched.child is None:
                return ChildContainer(None, node.node_id, base=base)
            content = await self.render(matched.child)
            return ChildContainer(content, node.node_id, matched.child.active_segment, base=base)

        async def slot(name: str, sub: MatchedNode) -> SlotContainer:
            return SlotContainer(await self.render(sub), node.node_id, name)

        jobs: dict[str, Awaitable[Any]] = {}
        if node.accepts_children or node.has_child_routes:
            jobs["children"] = child()
        for name, sub in matched.slots.items():
            jobs[name] = slot(name, sub)
        return dict(zip(jobs, await asyncio.gather(*jobs.values()), strict=True))

    async def _defer(self, node: RouteNode, matched: MatchedNode) -> ComponentTree:
        key = f"{node.node_id}@{self.nav_seq}"
        skeleton: ComponentTree = None
        if node.loading_layout is not None:
            skeleton = await _invoke_or_error(
                self.tree, node, node.loading_layout, node.loading_sig, matched.variables
            )
        route_payload: dict[str, Any] = {"node_id": node.node_id, "url": self.url}
        if self.extra_inputs:
            declared = _subtree_declared_inputs(self.tree, matched)
            filtered = {k: v for k, v in self.extra_inputs.items() if k in declared}
            if filtered:
                route_payload["extra"] = filtered
        return LazyContainer(skeleton, key, route=route_payload)


def _subtree_declared_inputs(tree: RouteTree, matched: MatchedNode) -> set[str]:
    declared: set[str] = set()
    for sub in matched.walk():
        if sub.mode != "empty":
            declared.update(tree.nodes[sub.node_id].query.names)
    return declared


async def fetch_endpoints(
    tree: RouteTree,
    subtrees: Iterable[MatchedNode | None],
    stop_at_lazy: bool,
    *,
    skip_root_lazy: bool = False,
) -> dict[str, Any]:
    """Run every `api.py` endpoint in `subtrees` concurrently; failures are returned as exceptions."""
    found = {
        node.node_id: (node, matched)
        for subtree in subtrees
        if subtree is not None
        for node, matched in _endpoint_nodes(tree, subtree, stop_at_lazy, skip_root_lazy=skip_root_lazy)
    }
    results = await asyncio.gather(
        *(invoke(node.endpoint, node.endpoint_sig, raw_vars=m.variables) for node, m in found.values()),  # type: ignore[arg-type]
        return_exceptions=True,
    )
    return dict(zip(found, results, strict=True))


def _endpoint_nodes(
    tree: RouteTree,
    matched: MatchedNode,
    stop_at_lazy: bool,
    *,
    skip_root_lazy: bool = False,
) -> Iterator[tuple[RouteNode, MatchedNode]]:
    if matched.mode != "page" or matched.omitted:
        return
    node = tree.nodes[matched.node_id]
    if stop_at_lazy and not skip_root_lazy and _is_lazy_boundary(node, matched):
        return
    if node.endpoint is not None:
        yield node, matched
    if matched.child is not None:
        yield from _endpoint_nodes(tree, matched.child, stop_at_lazy)
    for sub in matched.slots.values():
        yield from _endpoint_nodes(tree, sub, stop_at_lazy)


def _is_lazy_boundary(node: RouteNode, matched: MatchedNode) -> bool:
    return (
        matched.mode == "page"
        and not matched.omitted
        and (node.loading_layout is not None or node.layout_sig.is_streaming)
    )


def _has_container(tree: Any, container_id: ContainerId) -> bool:
    if isinstance(tree, list | tuple):
        return any(_has_container(item, container_id) for item in tree)
    if isinstance(tree, Component):
        return getattr(tree, "id", None) == container_id or _has_container(
            getattr(tree, "children", None), container_id
        )
    return False


def _check_children(node: RouteNode, matched: MatchedNode, output: ComponentTree) -> None:
    """Warn once per node when a child route is rendered but its layout never places `children`."""
    if matched.child is None or node.children_warned:
        return
    if _has_container(output, ChildContainer.ids.container(node.node_id)):
        return
    node.children_warned = True
    logger.warning(
        "Route '%s' renders a child route, but its layout does not place `children`. "
        "Add a `children` parameter to the layout and render it where the child route should appear.",
        node.node_id,
    )


async def _invoke_layout(tree: RouteTree, node: RouteNode, matched: MatchedNode, injected: dict[str, Any]) -> ComponentTree:
    try:
        output = await invoke(node.layout, node.layout_sig, raw_vars=matched.variables, injected=injected)
    except Exception as exc:
        return await render_error(tree, node, exc, matched.variables)
    _check_children(node, matched, output)
    return output


async def render_error(tree: RouteTree, node: RouteNode, error: BaseException, variables: dict[str, Any]) -> ComponentTree:
    err_layout = node.error_layout or tree.default_error_layout
    if err_layout is not None:
        sig = node.error_sig if node.error_layout is not None else tree.default_error_sig
        try:
            return await invoke(err_layout, sig, error, raw_vars=variables)
        except Exception:
            pass
    return html.Div(f"Error loading route: {error}", className="dash-router-error-banner")


async def _invoke_or_error(
    tree: RouteTree,
    node: RouteNode,
    target: Any,
    sig: FunctionSignatureInfo,
    variables: dict[str, Any],
    injected: dict[str, Any] | None = None,
) -> ComponentTree:
    try:
        return await invoke(target, sig, raw_vars=variables, injected=injected)
    except Exception as exc:
        return await render_error(tree, node, exc, variables)


async def _not_found(patches: list[PatchOp], layout: ErrorLayout | ComponentTree | None) -> PatchUpdate:
    if layout is None:
        content: ComponentTree = html.Div(html.H1("404 - Page not found"), className="dash-router-not-found")
    elif callable(layout):
        content = await invoke(layout, FunctionSignatureInfo.analyze(layout))
    else:
        content = layout
    return PatchUpdate(patches[0].target.container_id, content)


async def _next_item(generator: Any) -> Any:
    if inspect.isasyncgen(generator):
        return await anext(generator, _GEN_DONE)
    return next(generator, _GEN_DONE)


async def _close_generator(generator: Any) -> None:
    with suppress(Exception):
        if inspect.isasyncgen(generator):
            await generator.aclose()
        elif inspect.isgenerator(generator):
            generator.close()


# ─── EXECUTION ───────────────────────────────────────────────────────────────


async def execute_plan(
    tree: RouteTree, plan: TransitionPlan, not_found_layout: ErrorLayout | ComponentTree | None = None
) -> list[PatchUpdate]:
    """Render a plan eagerly in one step, lazy boundaries and streaming layouts included."""
    if not plan.matched:
        return [await _not_found(plan.patches, not_found_layout)]
    results = await fetch_endpoints(tree, (p.subtree for p in plan.patches), stop_at_lazy=False)
    renderer = _Renderer(tree, results)
    return list(await asyncio.gather(*(renderer.render_patch(p) for p in plan.patches)))


async def render_patches(
    tree: RouteTree,
    plan: TransitionPlan,
    patches: list[PatchOp],
    *,
    nav_seq: int = 0,
    extra_inputs: Mapping[str, Any] | None = None,
    not_found_layout: ErrorLayout | ComponentTree | None = None,
    path_prefix: str = "/",
) -> list[PatchUpdate]:
    """Render `patches` for a navigation response, deferring `loading.py` and generator nodes."""
    if not plan.matched:
        return [await _not_found(patches, not_found_layout)]
    results = await fetch_endpoints(tree, (p.subtree for p in patches), stop_at_lazy=True)
    renderer = _Renderer(
        tree,
        results,
        nav_seq=nav_seq,
        url=plan.new_url,
        extra_inputs=extra_inputs,
        lazy_boundaries=True,
        path_prefix=path_prefix,
    )
    return list(await asyncio.gather(*(renderer.render_patch(p) for p in patches)))


async def render_lazy(
    tree: RouteTree,
    node_id: str,
    url: str,
    extra_inputs: Mapping[str, Any] | None = None,
    *,
    nav_seq: int = 0,
    path_prefix: str = "/",
) -> AsyncGenerator[Any]:
    """Render one deferred `LazyContainer` subtree, streaming generator frames when applicable."""
    matched_tree = match_url(tree, url, extra_inputs)
    matched = matched_tree.root.find_node(node_id) if matched_tree is not None else None
    if matched is None or matched.mode != "page" or matched.omitted:
        yield None
        return

    node = tree.nodes[node_id]
    results = await fetch_endpoints(tree, [matched], stop_at_lazy=True, skip_root_lazy=True)
    data = results.get(node.node_id)
    if isinstance(data, BaseException):
        yield await render_error(tree, node, data, matched.variables)
        return

    renderer = _Renderer(
        tree,
        results,
        nav_seq=nav_seq,
        url=url,
        extra_inputs=extra_inputs,
        lazy_boundaries=True,
        skip_defer_node=node_id,
        path_prefix=path_prefix,
    )
    injected = {**await renderer._render_containers(node, matched), "data": data}
    if not node.layout_sig.is_streaming:
        yield await _invoke_layout(tree, node, matched, injected)
        return

    generator: Any = None
    first = True
    try:
        generator = start_callable(node.layout, node.layout_sig, raw_vars=matched.variables, injected=injected)
        while True:
            item = await _next_item(generator)
            if item is _GEN_DONE:
                if first:
                    yield None
                break
            if first:
                first = False
                if item is not None:
                    _check_children(node, matched, item)
                yield item
            else:
                # Subsequent `yield` (None) flushes `set_props` without wiping out frame 1.
                yield no_update if item is None else item
    except Exception as exc:
        yield await render_error(tree, node, exc, matched.variables)
    finally:
        await _close_generator(generator)
