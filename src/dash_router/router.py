import json
import logging
import sys
from collections.abc import AsyncIterator, Mapping
from pathlib import Path
from typing import Any

from dash import ALL, MATCH, Dash, Input, Output, State, callback_context, no_update
from dash.exceptions import PreventUpdate

from ._url_for import register_route_queries
from .components import CONTAINER_TYPE, LAZY_TYPE, RootContainer, container_key
from .core.execution import render_lazy, render_patches
from .core.matcher import MatchedTree, TransitionPlan, match_url, plan_transition, resolve_targets
from .core.params import parse_url, start_callable
from .core.tree import RouteTree
from .navigation import collect_route_query_keys, default_stubs_dir, generate_navigation_typing
from .types import ComponentTree, ErrorLayout

logger = logging.getLogger("dash_router")


class DashRouter:
    """File-system nested & parallel router for Dash 4.5+ on an async backend (Quart, FastAPI).

    Every URL change of the router's `dcc.Location` (links, `navigate()`, `UrlParam`, back /
    forward) runs one plain `Output(ALL)` callback. It diffs the new URL against the committed
    one and updates only the containers that changed, deferring `loading.py` boundaries and
    generator layouts to `LazyContainer`s loaded via a `MATCH` streaming callback.
    """

    def __init__(
        self,
        app: Dash | None = None,
        pages_folder: str | Path = "pages",
        *,
        tree: RouteTree | None = None,
        not_found_layout: ErrorLayout | ComponentTree | None = None,
        ignore_empty_folders: bool = False,
        generate_stubs: bool | None = None,
        stubs_dir: Path | None = None,
    ) -> None:
        if app is not None and not isinstance(app, Dash):
            raise TypeError(f"Expected a Dash instance, got {type(app).__name__}.")
        self.app = app
        self.not_found_layout = not_found_layout
        self._pages_folder: Path | None = _resolve_pages_path(app, pages_folder).resolve() if tree is None else None
        self._ignore_empty_folders = ignore_empty_folders
        self._generate_stubs = generate_stubs
        self._stubs_dir = stubs_dir
        self._excluded_inputs = _routing_input_names(app)
        self.tree = tree or RouteTree.from_folder(
            self._pages_folder,  # type: ignore[arg-type]
            ignore_empty_folders=ignore_empty_folders,
            default_error_layout=getattr(app, "_on_error", None),
        )
        self._sync_navigation_typing()
        if app is not None:
            self._bind(app)

    @classmethod
    def from_spec(
        cls,
        spec: Mapping[str, Any],
        app: Dash | None = None,
        not_found_layout: ErrorLayout | ComponentTree | None = None,
        *,
        generate_stubs: bool | None = None,
        stubs_dir: Path | None = None,
    ) -> "DashRouter":
        return cls(
            app,
            tree=RouteTree.from_spec(spec),
            not_found_layout=not_found_layout,
            generate_stubs=generate_stubs,
            stubs_dir=stubs_dir,
        )

    def reload(self) -> RouteTree:
        """Re-scan `pages_folder` and refresh route metadata and `url_for` type stubs."""
        if self._pages_folder is None:
            return self.tree
        self.tree = RouteTree.from_folder(
            self._pages_folder,
            ignore_empty_folders=self._ignore_empty_folders,
            default_error_layout=getattr(self.app, "_on_error", None),
        )
        self._sync_navigation_typing()
        return self.tree

    def _sync_navigation_typing(self) -> None:
        register_route_queries(collect_route_query_keys(self.tree, excluded_inputs=self._excluded_inputs))
        should_generate = (self._pages_folder is not None) if self._generate_stubs is None else self._generate_stubs
        if not should_generate:
            return
        out_dir = (
            self._stubs_dir
            if self._stubs_dir is not None
            else (default_stubs_dir(self._pages_folder) if self._pages_folder is not None else None)
        )
        project_root = out_dir.resolve().parent if out_dir is not None else None
        try:
            generate_navigation_typing(
                self.tree,
                output_dir=out_dir,
                excluded_inputs=self._excluded_inputs,
                project_root=project_root,
            )
        except OSError as exc:
            if self._generate_stubs is True:
                raise
            logger.debug("Skipping automatic dash_router stub generation: %s", exc)

    def match(self, url: str, extra_inputs: Mapping[str, Any] | None = None) -> MatchedTree | None:
        return match_url(self.tree, url, extra_inputs)

    def plan(
        self,
        old_url: str | None,
        new_url: str,
        extra_inputs: Mapping[str, Any] | None = None,
        prev_extra_inputs: Mapping[str, Any] | None = None,
    ) -> TransitionPlan:
        return plan_transition(self.tree, old_url, new_url, extra_inputs, prev_extra_inputs)

    # ─── DASH WIRING ─────────────────────────────────────────────────────────

    def _bind(self, app: Dash) -> None:
        setattr(app, "router", self)
        app.clientside_callback(
            "function(d) { if (d && d.title) document.title = d.title; }",
            Input(RootContainer.ids.committed_store, "data"),
            prevent_initial_call=True,
            hidden=True,
        )
        inputs: dict[str, Any] = {
            "pathname_": Input(RootContainer.ids.location, "pathname"),
            "search_": Input(RootContainer.ids.location, "search"),
            "committed_": State(RootContainer.ids.committed_store, "data"),
        }
        routing_inputs = getattr(app, "routing_callback_inputs", None)
        if isinstance(routing_inputs, dict):
            inputs.update(routing_inputs)
        app.callback(
            Output({"type": CONTAINER_TYPE, "index": ALL}, "children"),
            Output(RootContainer.ids.committed_store, "data"),
            inputs=inputs,
            hidden=True,
        )(self._navigate)
        app.callback(
            Output({"type": LAZY_TYPE, "index": MATCH}, "children"),
            Input({"type": LAZY_TYPE, "index": MATCH}, "data-route"),
            State({"type": LAZY_TYPE, "index": MATCH}, "id"),
            stream=True,
            hidden=True,
        )(self._load_lazy)

    async def _navigate(
        self, pathname_: str | None, search_: str | None, committed_: dict[str, Any] | None, **extra: Any
    ) -> tuple[list[Any], dict[str, Any]]:
        url = self._route_url(pathname_, search_)
        committed = committed_ if isinstance(committed_, dict) else {}
        if committed.get("url") == url and committed.get("extra", {}) == extra:
            raise PreventUpdate

        raw_specs = callback_context.outputs_grouping[0]
        container_specs: list[dict[str, Any]] = (
            [raw_specs] if isinstance(raw_specs, dict) else list(raw_specs or [])
        )
        existing_keys = {container_key(spec["id"]) for spec in container_specs}

        plan = self.plan(committed.get("url"), url, extra or None, committed.get("extra"))
        patches = resolve_targets(plan, existing_keys)
        seq = int(committed.get("seq") or 0) + 1
        updates = await render_patches(
            self.tree,
            plan,
            patches,
            nav_seq=seq,
            extra_inputs=extra or None,
            not_found_layout=self.not_found_layout,
            path_prefix=self._path_prefix(),
        )
        by_key = {container_key(upd.container_id): upd.children for upd in updates}
        containers_out = [by_key.get(container_key(spec["id"]), no_update) for spec in container_specs]

        # `href` is the address as the browser shows it: the client compares it with `location` to tell
        # whether a navigation is still in flight.
        href = (pathname_ or "/") + (search_ or "")
        committed_data: dict[str, Any] = {"url": url, "href": href, "seq": seq, "extra": extra}
        if (title := self._title(plan)) is not None:
            committed_data["title"] = title
        return containers_out, committed_data

    async def _load_lazy(
        self, route_json: str | None, component_id: dict[str, Any] | None
    ) -> AsyncIterator[Any]:
        if not route_json:
            return
        payload = json.loads(route_json)
        index = (component_id or {}).get("index", "")
        nav_seq = int(index.rsplit("@", 1)[1]) if "@" in index and index.rsplit("@", 1)[1].isdigit() else 0
        async for item in render_lazy(
            self.tree,
            payload["node_id"],
            payload["url"],
            payload.get("extra"),
            nav_seq=nav_seq,
            path_prefix=self._path_prefix(),
        ):
            yield item

    def _path_prefix(self) -> str:
        return getattr(getattr(self.app, "config", None), "requests_pathname_prefix", None) or "/"

    def _route_url(self, pathname: str | None, search: str | None) -> str:
        path = pathname or "/"
        prefix = self._path_prefix()
        if prefix != "/" and path.startswith(prefix):
            path = "/" + path[len(prefix) :]
        return parse_url(path)[0] + (search or "")

    def _title(self, plan: TransitionPlan) -> str | None:
        """Title of the deepest node on the main route chain that sets one."""
        title: str | None = None
        matched = plan.new_tree.root if plan.new_tree is not None else None
        while matched is not None:
            node = self.tree.nodes[matched.node_id]
            configured = node.config.title
            if isinstance(configured, str):
                title = configured
            elif configured is not None:
                try:
                    title = str(start_callable(configured, node.title_sig, raw_vars=matched.variables))
                except Exception:
                    pass
            matched = matched.child
        return title


def _routing_input_names(app: Dash | None) -> frozenset[str]:
    if app is None:
        return frozenset()
    routing_inputs = getattr(app, "routing_callback_inputs", None)
    return frozenset(routing_inputs) if isinstance(routing_inputs, dict) else frozenset()


def _resolve_pages_path(app: Dash | None, pages_folder: str | Path) -> Path:
    raw = Path(pages_folder)
    if raw.is_absolute() or raw.exists() or app is None:
        return raw
    configured = getattr(app.config, "pages_folder", None)
    if configured and Path(configured).exists():
        return Path(configured)
    module = sys.modules.get(getattr(app.config, "name", None) or "")
    module_file = getattr(module, "__file__", None)
    if module_file and (candidate := Path(module_file).resolve().parent / raw).exists():
        return candidate
    return raw
