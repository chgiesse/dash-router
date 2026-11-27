import asyncio
import json
import time
from collections.abc import AsyncIterator
from enum import Enum
from typing import Any

import pytest
from dash import html, no_update
from dash._utils import to_json
from dash.development.base_component import Component
from pydantic import BaseModel

from dash_router import DashRouter, LazyContainer, RootContainer, RouteTester
from dash_router.components import LAZY_TYPE
from dash_router.core.execution import render_lazy, render_patches


def _all_lazy(tree: Any) -> list[LazyContainer]:
    found: list[LazyContainer] = []
    stack: list[Any] = [tree]
    while stack:
        cur = stack.pop()
        if isinstance(cur, LazyContainer):
            found.append(cur)
        if isinstance(cur, Component):
            for prop in getattr(cur, "_prop_names", ()):
                val = getattr(cur, prop, None)
                if isinstance(val, Component | list | tuple):
                    stack.append(val)
        elif isinstance(cur, list | tuple):
            stack.extend(cur)
    return found


def _has_lazy_boundary(tree: Any) -> bool:
    return bool(_all_lazy(tree))


def _lazy_id(lazy: Any) -> dict[str, str]:
    return lazy.to_plotly_json()["props"]["id"]


async def _collect(frames: AsyncIterator[Any]) -> list[Any]:
    return [frame async for frame in frames]


class Period(Enum):
    DAILY = "daily"
    MONTHLY = "monthly"


class AnalyticsFilters(BaseModel):
    period: Period = Period.MONTHLY
    limit: int = 10
    tags: list[str] = []


def test_pydantic_and_typed_query_param_coercion_and_diffing():
    captured_calls: list[dict[str, Any]] = []

    async def analytics_endpoint(filters: AnalyticsFilters, search_term: str | None = None):
        payload = {
            "period": filters.period.value,
            "limit": filters.limit,
            "tags": filters.tags,
            "search_term": search_term,
        }
        captured_calls.append(payload)
        return payload

    async def analytics_layout(data: dict[str, object]):
        return html.Div(f"{data['period']}:{data['limit']}:{data['search_term']}")

    tester = RouteTester.from_spec(
        {
            "sales": {
                "analytics": {
                    "endpoint": analytics_endpoint,
                    "layout": analytics_layout,
                },
            },
        }
    )

    # 1. Unrelated query param `?unrelated=1` does NOT trigger re-render of `sales/analytics`!
    tester.assert_routes(
        old="/sales/analytics?period=daily&limit=25",
        new="/sales/analytics?period=daily&limit=25&unrelated=foo",
        expected=[],
    )

    # 2. Updating a Pydantic model field (`limit=50`) triggers `sales/analytics` ONLY (`sales` stays mounted!)
    res = tester.assert_routes(
        old="/sales/analytics?period=daily&limit=25",
        new="/sales/analytics?period=daily&limit=50&tags=eu&tags=us&search_term=risk",
        expected=["sales/analytics"],
    )

    updates = asyncio.run(res.render())
    assert len(updates) == 1
    assert captured_calls[-1] == {
        "period": "daily",
        "limit": 50,
        "tags": ["eu", "us"],
        "search_term": "risk",
    }

    # 3. Clearing `search_term` from query string triggers re-render with `search_term=None`
    res_cleared = tester.assert_routes(
        old="/sales/analytics?period=daily&limit=50&search_term=risk",
        new="/sales/analytics?period=daily&limit=50",
        expected=["sales/analytics"],
    )
    asyncio.run(res_cleared.render())
    assert captured_calls[-1]["search_term"] is None


def test_endpoint_without_var_kwargs_and_isolated_error_boundaries():
    # Endpoint without `**kwargs` must NOT crash when parent `[team_id]` or unrelated query params exist!
    async def strict_ok_endpoint(region: str = "eu") -> str:
        return f"ok:{region}"

    async def failing_endpoint() -> str:
        raise ValueError("database timeout")

    def custom_error_layout(exc: Exception, team_id: str | None = None) -> html.Div:
        return html.Div(f"Handled({team_id}): {exc}", className="custom-err")

    tester = RouteTester.from_spec(
        {
            "projects": {
                "[team_id]": {
                    "(healthy)": {
                        "endpoint": strict_ok_endpoint,
                        "layout": lambda data: html.Div(data, id="healthy-slot"),
                    },
                    "(broken)": {
                        "endpoint": failing_endpoint,
                        "layout": lambda data: html.Div(data, id="broken-slot"),
                        "error": custom_error_layout,
                    },
                },
            },
        }
    )

    res = tester.transition(old=None, new="/projects/alpha?region=apac&extra=ignored")
    updates = asyncio.run(res.render())
    assert len(updates) == 1
    rendered_json = str(to_json(updates[0].children))
    assert "ok:apac" in rendered_json
    assert "Handled(alpha): database timeout" in rendered_json


def test_streaming_lazy_boundaries_and_parallel_endpoints():
    async def slow_slot_a() -> str:
        await asyncio.sleep(0.06)
        return "slot-a-ready"

    async def slow_slot_b() -> str:
        await asyncio.sleep(0.06)
        return "slot-b-ready"

    router = DashRouter.from_spec(
        {
            "dashboard": {
                "(ranks)": {
                    "loading": html.Div("Loading ranks..."),
                    "endpoint": slow_slot_a,
                    "layout": lambda data: html.Div(data),
                },
                "(revenue)": {
                    "loading": lambda: html.Div("Loading revenue..."),
                    "endpoint": slow_slot_b,
                    "layout": lambda data: html.Div(data),
                },
            },
        }
    )

    # The navigation response mounts the loading boundaries as LazyContainer skeletons without running their endpoints.
    plan = router.plan(None, "/dashboard")
    [root] = asyncio.run(render_patches(router.tree, plan, plan.patches))
    assert root.container_id == RootContainer.ids.container
    root_str = str(to_json(root.children))
    assert "Loading ranks..." in root_str
    assert "Loading revenue..." in root_str
    assert sorted(_lazy_id(lazy)["index"] for lazy in _all_lazy(root.children)) == [
        "dashboard/(ranks)@0",
        "dashboard/(revenue)@0",
    ]

    # Each LazyContainer then loads through `render_lazy`; both 60ms endpoints run concurrently (not a 120ms waterfall).
    async def _load_both() -> tuple[list[Any], list[Any]]:
        return await asyncio.gather(
            _collect(render_lazy(router.tree, "dashboard/(ranks)", "/dashboard")),
            _collect(render_lazy(router.tree, "dashboard/(revenue)", "/dashboard")),
        )

    t0 = time.perf_counter()
    ranks, revenue = asyncio.run(_load_both())
    elapsed = time.perf_counter() - t0

    assert "slot-a-ready" in str(to_json(ranks))
    assert "slot-b-ready" in str(to_json(revenue))
    assert elapsed < 0.14


def test_streaming_navigation_updates_children_and_discovers_regular_and_no_output_callbacks():
    import json
    import re
    import shutil
    import subprocess
    from pathlib import Path
    from typing import cast

    from dash import Dash, Input, Output, set_props
    from quart import Quart

    renderer_dir = Path(__file__).resolve().parents[3] / "packages" / "dash" / "dash" / "dash-renderer"
    if shutil.which("node") is None:
        pytest.skip("node is required for the dash-renderer harness")
    if not (renderer_dir / "node_modules" / "@babel" / "core").is_dir():
        pytest.skip("dash-renderer's node_modules (@babel/core) are required for the harness")

    async def slow_cart_endpoint() -> str:
        await asyncio.sleep(0.005)
        return "cart-loaded"

    def cart_layout(data: str = "", **_: Any):
        return html.Div(
            [
                html.Div(data, id="cart-data"),
                html.Div("seed", id="mounted-in"),
                html.Div(id="mounted-out"),
                html.Div("trigger", id="mounted-no-out"),
                html.Div(id="no-out-target"),
                html.Div("skip", id="prevent-in"),
                html.Div(id="prevent-out"),
                html.Div(id="plain-target"),
            ],
            id="cart-root",
        )

    quart_server = Quart(__name__)
    app = Dash(__name__, server=cast(Any, quart_server), use_pages=False, suppress_callback_exceptions=True)
    DashRouter.from_spec(
        {
            "shop": {
                "title": "Shop · Cart",
                "endpoint": slow_cart_endpoint,
                "loading": html.Div("Loading cart...", id="cart-skeleton"),
                "layout": cart_layout,
            }
        },
        app=app,
    )
    app.layout = html.Div([RootContainer(), html.Div(id="outside-out")])

    @app.callback(Output("mounted-out", "children"), Input("mounted-in", "children"))
    async def _regular_cb(val: str) -> str:
        # Plain `set_props` mounts new components, but their initial calls don't run.
        set_props("plain-target", {"children": html.Div([html.Div("seed", id="plain-in"), html.Div(id="plain-out")])})
        return f"regular:{val}"

    # Input inside the streamed content, output outside it: mounting the input is no change.
    @app.callback(Output("outside-out", "children"), Input("mounted-in", "children"), prevent_initial_call=True)
    async def _outside_cb(val: str) -> str:
        return f"outside:{val}"

    # noOutput callbacks do not run an initial call on dynamic mount (stock Dash behavior).
    @app.callback(Input("mounted-no-out", "children"))
    async def _no_output_cb(val: str) -> None:
        set_props("no-out-target", {"children": f"no-output:{val}"})

    @app.callback(Output("plain-out", "children"), Input("plain-in", "children"))
    async def _plain_cb(val: str) -> str:
        return val

    @app.callback(Output("prevent-out", "children"), Input("prevent-in", "children"), prevent_initial_call=True)
    async def _prevented_cb(val: str) -> str:
        return f"prevented:{val}"

    async def _collect_quart_fixtures() -> tuple[dict[str, Any], list[Any], str, str, str, dict[str, str]]:
        client = quart_server.test_client()
        index_html = await (await client.get("/shop")).get_data(as_text=True)
        inline_scripts = "\n".join(
            s
            for s in re.findall(r"<script[^>]*>(.*?)</script>", index_html, re.DOTALL)
            if "_dashprivate_clientside_funcs" in s
        )
        layout_json = await (await client.get("/_dash-layout")).get_json()
        deps_json = await (await client.get("/_dash-dependencies")).get_json()
        router_output = next(
            key for key in app.callback_map if RootContainer.ids.location in str(app.callback_map[key]["inputs"])
        )
        lazy_output = next(key for key in app.callback_map if LAZY_TYPE in key)

        # The navigation is a plain callback: the router mounts the shell with the cart's LazyContainer.
        nav_resp = await client.post(
            "/_dash-update-component",
            data=json.dumps(
                {
                    "output": router_output,
                    "outputs": [
                        [{"id": RootContainer.ids.container, "property": "children"}],
                        {"id": RootContainer.ids.committed_store, "property": "data"},
                    ],
                    "inputs": [
                        {"id": RootContainer.ids.location, "property": "pathname", "value": "/shop"},
                        {"id": RootContainer.ids.location, "property": "search", "value": ""},
                    ],
                    "changedPropIds": [f"{RootContainer.ids.location}.pathname"],
                    "state": [{"id": RootContainer.ids.committed_store, "property": "data", "value": None}],
                }
            ),
            headers={"Content-Type": "application/json"},
        )
        nav_body = await nav_resp.get_data(as_text=True)

        # The LazyContainer mounts and its `MATCH` streaming callback delivers the cart.
        lazy_id = LazyContainer.ids.container("shop@1")
        route = json.dumps({"node_id": "shop", "url": "/shop"}, separators=(",", ":"), sort_keys=True)
        lazy_resp = await client.post(
            "/_dash-update-component",
            data=json.dumps(
                {
                    "output": lazy_output,
                    "outputs": {"id": lazy_id, "property": "children"},
                    "inputs": [{"id": lazy_id, "property": "data-route", "value": route}],
                    "changedPropIds": [],
                    "state": [{"id": lazy_id, "property": "id", "value": lazy_id}],
                }
            ),
            headers={"Content-Type": "application/json"},
        )
        lazy_body = await lazy_resp.get_data(as_text=True)

        regular_resp = await client.post(
            "/_dash-update-component",
            data=json.dumps(
                {
                    "output": "mounted-out.children",
                    "outputs": {"id": "mounted-out", "property": "children"},
                    "inputs": [{"id": "mounted-in", "property": "children", "value": "seed"}],
                    "changedPropIds": [],
                }
            ),
            headers={"Content-Type": "application/json"},
        )
        cb_responses = {
            "mounted-out.children": await regular_resp.get_data(as_text=True),
            router_output: nav_body,
            lazy_output: lazy_body,
        }
        return layout_json, deps_json, router_output, lazy_output, inline_scripts, cb_responses

    layout_json, deps_json, router_output, lazy_output, inline_scripts, cb_responses = asyncio.run(
        _collect_quart_fixtures()
    )

    harness_js = f"""
    const fs = require("fs");
    const path = require("path");
    const Module = require("module");
    const rendererDir = {json.dumps(str(renderer_dir))};
    const nm = path.join(rendererDir, "node_modules");
    module.paths.unshift(nm);
    const babel = require("@babel/core");

    const origResolve = Module._resolveFilename;
    Module._resolveFilename = function(req, parent, isMain, opts) {{
      if (parent && parent.filename && parent.filename.startsWith(rendererDir) && req.startsWith(".")) {{
        const base = path.resolve(path.dirname(parent.filename), req);
        for (const ext of ["", ".ts", ".tsx", ".js", ".jsx", "/index.ts", "/index.js"]) {{
          if (fs.existsSync(base + ext) && fs.statSync(base + ext).isFile()) return base + ext;
        }}
      }}
      return origResolve.call(this, req, parent, isMain, opts);
    }};
    for (const ext of [".js", ".jsx", ".ts", ".tsx"]) {{
      Module._extensions[ext] = function(mod, filename) {{
        if (filename.includes("node_modules")) return mod._compile(fs.readFileSync(filename, "utf8"), filename);
        const out = babel.transformSync(fs.readFileSync(filename, "utf8"), {{
          filename,
          presets: [
            [path.join(nm, "@babel/preset-env"), {{ targets: {{ node: "current" }}, modules: "commonjs" }}],
            [path.join(nm, "@babel/preset-react"), {{ runtime: "automatic" }}],
            [path.join(nm, "@babel/preset-typescript"), {{ allowDeclareFields: true }}],
          ],
        }});
        return mod._compile(out.code, filename);
      }};
    }}
    Module._extensions[".css"] = (m) => m._compile("module.exports = {{}};", "");
    Module._extensions[".svg"] = (m) => m._compile("module.exports = () => null;", "");

    const React = require("react");
    const {{ renderToStaticMarkup }} = require("react-dom/server");
    const {{ Provider }} = require("react-redux");

    const cbResponses = {json.dumps(cb_responses)};
    const routerOutput = {json.dumps(router_output)};
    const lazyOutput = {json.dumps(lazy_output)};
    const dispatchedRequests = [];

    global.window = global;
    global.self = global;
    global.MutationObserver = class {{ observe() {{}} disconnect() {{}} }};
    global.document = {{ cookie: "", title: "initial", querySelector: () => null }};
    window.location = {{ pathname: "/shop", search: "", hash: "", href: "http://localhost/shop" }};
    window.dash_html_components = {{
      Div: ({{ children, id }}) => React.createElement("div", {{ id: typeof id === "string" ? id : JSON.stringify(id) }}, children),
    }};
    window.dash_core_components = {{ Location: () => null, Store: () => null }};

    global.fetch = async (_url, init) => {{
      const body = JSON.parse(init.body);
      dispatchedRequests.push({{ output: body.output, changedPropIds: body.changedPropIds }});
      if (body.output === routerOutput) {{
        return new Response(cbResponses[routerOutput], {{
          status: 200,
          headers: {{ "Content-Type": "application/json" }},
        }});
      }}
      if (body.output === lazyOutput) {{
        return new Response(cbResponses[lazyOutput], {{
          status: 200,
          headers: {{ "Content-Type": "application/x-ndjson" }},
        }});
      }}
      return new Response(cbResponses[body.output] || "{{}}", {{
        status: 200,
        headers: {{ "Content-Type": "application/json" }},
      }});
    }};

    require(path.join(rendererDir, "src/dashApi.ts"));
    {inline_scripts}
    const Store = require(path.join(rendererDir, "src/store.ts")).default;
    const {{ setConfig, setLayout, setPaths, setGraphs, hydrateInitialOutputs, notifyObservers }} = require(path.join(rendererDir, "src/actions/index.js"));
    const {{ computePaths, getPath }} = require(path.join(rendererDir, "src/actions/paths.js"));
    const {{ computeGraphs }} = require(path.join(rendererDir, "src/actions/dependencies.js"));
    const DashWrapper = require(path.join(rendererDir, "src/wrapper/DashWrapper.tsx")).default;

    (async () => {{
      const store = new Store().store;
      const cfg = {{
        url_base_pathname: "/",
        requests_pathname_prefix: "/",
        ui: false,
        props_check: false,
        suppress_callback_exceptions: true,
        update_title: null,
        children_props: {{ dash_html_components: {{}}, dash_core_components: {{}} }},
        fetch: {{ headers: {{}} }},
      }};
      store.dispatch(setConfig(cfg));
      const initialLayout = {json.dumps(layout_json)};
      store.dispatch(setPaths(computePaths(initialLayout, ["components"], null, {{ emit() {{}}, once(_e, fn) {{ fn(); }} }})));
      store.dispatch(setLayout(initialLayout));
      store.dispatch(setGraphs(computeGraphs({json.dumps(deps_json)}, () => {{}}, cfg)));
      store.dispatch(hydrateInitialOutputs());

      // Trigger the router's location change to /shop: the navigation mounts the cart's LazyContainer.
      store.dispatch(notifyObservers({{ id: {json.dumps(RootContainer.ids.location)}, props: {{ pathname: "/shop" }} }}));

      await new Promise(r => setTimeout(r, 80));

      const state = store.getState();
      const lazyId = {json.dumps(LazyContainer.ids.container("shop@1"))};
      const lazyPath = getPath(state.paths, lazyId);

      // Simulate React's first render of LazyContainer when the lazy response already updated Redux (`h > 0`)
      // while the parent still passes the stale skeleton as `_passedComponent`.
      const stalePassed = {{
        type: "Div",
        namespace: "dash_html_components",
        props: {{ id: lazyId, children: "STALE_SKELETON" }},
      }};
      const markup = renderToStaticMarkup(
        React.createElement(
          Provider,
          {{ store }},
          React.createElement(DashWrapper, {{
            componentPath: lazyPath,
            _passedComponent: stalePassed,
            _newRender: {{}},
          }})
        )
      );

      const getText = id => window.dash_component_api.getLayout(id)?.props?.children;
      console.log(JSON.stringify({{
        title: document.title,
        dispatched: dispatchedRequests,
        cartData: getText("cart-data"),
        mountedOut: getText("mounted-out"),
        noOutTarget: getText("no-out-target"),
        plainRegistered: Boolean(getPath(store.getState().paths, "plain-in")),
        committed: window.dash_component_api.getLayout({json.dumps(RootContainer.ids.committed_store)})?.props?.data,
        lazyMarkup: markup,
      }}));
    }})();
    """

    proc = subprocess.run(["node", "-e", harness_js], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    out = json.loads(proc.stdout)

    assert out["title"] == "Shop · Cart"
    assert out["cartData"] == "cart-loaded"
    assert out["mountedOut"] == "regular:seed"
    assert out["noOutTarget"] is None
    assert out["plainRegistered"]
    # The navigation commits its URL without any pending bookkeeping.
    assert out["committed"]["url"] == "/shop"
    assert "pending" not in out["committed"]
    assert "STALE_SKELETON" not in out["lazyMarkup"]
    assert "cart-loaded" in out["lazyMarkup"]
    # Only the initial call of the regular Output callback inside the streamed content ran,
    # without spurious changedPropIds: not prevent_initial_call=True, not noOutput, not output outside
    # the content, and not the callback mounted by a plain set_props.
    cb_dispatches = [d for d in out["dispatched"] if d["output"] not in (router_output, lazy_output)]
    assert [d["output"] for d in cb_dispatches] == ["mounted-out.children"]
    assert all(d["changedPropIds"] == [] for d in cb_dispatches)


def test_render_patches_defers_loading_nodes_and_generator_layouts():
    async def gen_layout(**_: Any):
        yield html.Div("streamed")

    router = DashRouter.from_spec(
        {
            "loader": {"loading": html.Div("loader-skeleton"), "layout": lambda **_: html.Div("loaded")},
            "streamer": {"layout": gen_layout},
        }
    )

    loader_plan = router.plan(None, "/loader")
    [loader] = asyncio.run(render_patches(router.tree, loader_plan, loader_plan.patches, nav_seq=7))
    assert isinstance(loader.children, LazyContainer)
    assert _lazy_id(loader.children) == LazyContainer.ids.container("loader@7")
    assert "loader-skeleton" in str(to_json(loader.children))
    assert "loaded" not in str(to_json(loader.children))
    assert json.loads(getattr(loader.children, "data-route")) == {"node_id": "loader", "url": "/loader"}

    streamer_plan = router.plan(None, "/streamer")
    [streamer] = asyncio.run(render_patches(router.tree, streamer_plan, streamer_plan.patches, nav_seq=2))
    assert isinstance(streamer.children, LazyContainer)
    assert _lazy_id(streamer.children) == LazyContainer.ids.container("streamer@2")
    assert json.loads(getattr(streamer.children, "data-route")) == {"node_id": "streamer", "url": "/streamer"}


def test_render_patches_filters_extra_to_the_names_declared_by_the_lazy_subtree():
    router = DashRouter.from_spec(
        {
            "reports": {
                "inputs": ["period"],
                "loading": html.Div("spin"),
                "layout": lambda **_: html.Div("reports"),
                "(side)": {"inputs": ["tab"], "layout": lambda **_: html.Div("side")},
            },
        }
    )
    extra = {"period": "daily", "tab": "x", "unrelated": "1"}
    plan = router.plan(None, "/reports", extra)
    [update] = asyncio.run(render_patches(router.tree, plan, plan.patches, nav_seq=1, extra_inputs=extra))
    assert json.loads(getattr(update.children, "data-route")) == {
        "node_id": "reports",
        "url": "/reports",
        "extra": {"period": "daily", "tab": "x"},
    }

    undeclared_only = {"unrelated": "1"}
    plan = router.plan(None, "/reports", undeclared_only)
    [update] = asyncio.run(render_patches(router.tree, plan, plan.patches, extra_inputs=undeclared_only))
    assert json.loads(getattr(update.children, "data-route")) == {"node_id": "reports", "url": "/reports"}


def test_render_lazy_renders_nested_lazy_boundaries_one_level_at_a_time():
    router = DashRouter.from_spec(
        {
            "outer": {
                "loading": html.Div("outer-skeleton"),
                "layout": lambda children=None, **_: html.Div(["outer-ready", children]),
                "inner": {"loading": html.Div("inner-skeleton"), "layout": lambda **_: html.Div("inner-ready")},
            },
        }
    )

    [outer] = asyncio.run(_collect(render_lazy(router.tree, "outer", "/outer/inner")))
    assert "outer-ready" in str(to_json(outer))
    assert "inner-skeleton" in str(to_json(outer))
    assert "inner-ready" not in str(to_json(outer))
    assert [_lazy_id(lazy)["index"] for lazy in _all_lazy(outer)] == ["outer/inner@0"]

    [inner] = asyncio.run(_collect(render_lazy(router.tree, "outer/inner", "/outer/inner")))
    assert "inner-ready" in str(to_json(inner))


def test_render_lazy_renders_an_error_boundary_when_the_endpoint_fails():
    async def failing_endpoint() -> str:
        raise ValueError("database timeout")

    router = DashRouter.from_spec(
        {"reports": {"loading": html.Div("spin"), "endpoint": failing_endpoint, "layout": lambda data: html.Div(data)}}
    )
    [frame] = asyncio.run(_collect(render_lazy(router.tree, "reports", "/reports")))
    assert "Error loading route: database timeout" in str(to_json(frame))


def test_render_lazy_streams_async_and_sync_generator_frames_and_error_boundaries():
    async def multi_comp_gen(**kwargs: Any):
        yield html.Div("comp-0")
        await asyncio.sleep(0.01)
        yield html.Div("comp-1")

    def sync_gen(**kwargs: Any):
        yield html.Div("sync-1")
        yield html.Div("sync-2")

    async def failing_after_yield(**kwargs: Any):
        yield html.Div("loading-first")
        await asyncio.sleep(0.01)
        raise ValueError("boom after yield")

    def err_layout(error: Exception, **kwargs: Any):
        return html.Div(f"caught:{error}")

    router = DashRouter.from_spec(
        {
            "multi": {"layout": multi_comp_gen},
            "sync": {"layout": sync_gen},
            "fail": {"layout": failing_after_yield, "error": err_layout},
        }
    )

    # Eager rendering takes a generator layout's first item.
    eager_sync = asyncio.run(RouteTester(router).transition(None, "/sync").render())
    assert "sync-1" in str(to_json(eager_sync[0].children))

    multi = asyncio.run(_collect(render_lazy(router.tree, "multi", "/multi", nav_seq=1)))
    assert len(multi) == 2
    assert "comp-0" in str(to_json(multi[0]))
    assert "comp-1" in str(to_json(multi[1]))

    sync = asyncio.run(_collect(render_lazy(router.tree, "sync", "/sync")))
    assert "sync-1" in str(to_json(sync[0]))
    assert "sync-2" in str(to_json(sync[1]))

    # An error after the first yield renders the node's own error boundary in place of the stream.
    fail = asyncio.run(_collect(render_lazy(router.tree, "fail", "/fail", nav_seq=2)))
    assert len(fail) == 2
    assert "loading-first" in str(to_json(fail[0]))
    assert "caught:boom after yield" in str(to_json(fail[1]))


def test_render_lazy_closes_the_generator_when_the_stream_is_closed():
    gate = asyncio.Event()
    closed_count = 0

    async def slot_gen(**kwargs: Any):
        nonlocal closed_count
        try:
            yield html.Div("gen-skel")
            await gate.wait()
            yield
        finally:
            closed_count += 1

    router = DashRouter.from_spec(
        {
            "orders": {
                "(feed)": {"layout": slot_gen},
                "[id]": {},
            }
        }
    )

    async def _run() -> int:
        frames = render_lazy(router.tree, "orders/(feed)", "/orders")
        frame0 = await anext(frames)
        assert "gen-skel" in str(to_json(frame0))
        await frames.aclose()
        return closed_count

    assert asyncio.run(_run()) == 1


def test_async_generator_layout_streams_set_props_patches_after_the_first_frame():
    from dash import Patch, set_props
    from dash._callback_context import context_value
    from dash._utils import AttributeDict

    step1 = asyncio.Event()
    step2 = asyncio.Event()

    async def table_layout(**kwargs: Any):
        yield html.Table([html.Tbody(html.Tr(html.Td("skeleton")), id="tbl-body")])
        await step1.wait()
        set_props("tbl-body", {"children": [html.Tr(html.Td("row-1"))]})
        yield
        await step2.wait()
        p = Patch()
        p.append(html.Tr(html.Td("row-2")))
        set_props("tbl-body", {"children": p})
        yield

    router = DashRouter.from_spec({"metrics": {"layout": table_layout}})

    async def _run() -> tuple[list[Any], list[dict[str, Any]], list[Any]]:
        ctx = AttributeDict({"updated_props": {}})
        token = context_value.set(ctx)
        flushed_side_updates: list[dict[str, Any]] = []
        frames: list[Any] = []
        try:
            stream = render_lazy(router.tree, "metrics", "/metrics", nav_seq=5)
            frames.append(await anext(stream))
            # The first frame is the layout itself, not a LazyContainer, and nothing has been flushed yet.
            assert not _has_lazy_boundary(frames[0])
            assert ctx.updated_props == {}

            step1.set()
            frames.append(await anext(stream))
            flushed_side_updates.append(dict(ctx.updated_props))
            ctx.updated_props.clear()

            step2.set()
            frames.append(await anext(stream))
            flushed_side_updates.append(dict(ctx.updated_props))
            ctx.updated_props.clear()

            with pytest.raises(StopAsyncIteration):
                await anext(stream)
        finally:
            context_value.reset(token)

        ctx2 = AttributeDict({"updated_props": {}})
        token2 = context_value.set(ctx2)
        try:
            step1.set()
            step2.set()
            eager = await RouteTester(router).transition(None, "/metrics").render()
        finally:
            context_value.reset(token2)
        return frames, flushed_side_updates, eager

    frames, side_updates, eager = asyncio.run(_run())
    assert len(frames) == 3
    assert "skeleton" in str(to_json(frames[0]))
    # Bare yields after the first frame become `no_update`, so Dash flushes the `set_props` without replacing frame 1.
    assert frames[1] is no_update
    assert "row-1" in str(to_json(side_updates[0]["tbl-body"]["children"]))
    assert frames[2] is no_update
    assert "tbl-body" in side_updates[1]
    assert "skeleton" in str(to_json(eager[0].children))


def test_loading_endpoint_and_generator_layout_stream_after_the_initial_batch():
    from dash import set_props
    from dash._callback_context import context_value
    from dash._utils import AttributeDict

    ep_gate = asyncio.Event()
    tick_gate = asyncio.Event()

    async def ep(**kwargs: Any) -> list[int]:
        await ep_gate.wait()
        return [1, 2]

    async def gen_layout(data: list[int], **kwargs: Any):
        yield html.Div(f"initial:{data}", id="chart")
        step = 1
        while True:
            await tick_gate.wait()
            set_props("chart", {"children": f"tick:{step}"})
            step += 1
            yield

    router = DashRouter.from_spec(
        {
            "dash": {
                "endpoint": ep,
                "loading": html.Div("spinner"),
                "layout": gen_layout,
            }
        }
    )

    async def _run() -> tuple[Any, Any, dict[str, Any], list[Any]]:
        ctx = AttributeDict({"updated_props": {}})
        tok = context_value.set(ctx)
        try:
            plan = router.plan(None, "/dash")
            [f0] = await render_patches(router.tree, plan, plan.patches, nav_seq=3)
            ep_gate.set()
            stream = render_lazy(router.tree, "dash", "/dash", nav_seq=3)
            f1 = await anext(stream)
            tick_gate.set()
            f2 = await anext(stream)
            assert f2 is no_update
            side = dict(ctx.updated_props)
            await stream.aclose()
        finally:
            context_value.reset(tok)

        eager = await RouteTester(router).transition(None, "/dash").render()
        return f0, f1, side, eager

    f0, f1, side, eager = asyncio.run(_run())
    assert "spinner" in str(to_json(f0.children))
    assert _lazy_id(f0.children) == LazyContainer.ids.container("dash@3")
    assert "initial:[1, 2]" in str(to_json(f1))
    assert side["chart"]["children"] == "tick:1"
    assert "initial:[1, 2]" in str(to_json(eager[0].children))


def test_collection_inputs_use_comma_separated_lists_like_url_param():
    from dash_router import Url

    seen: list[list[str]] = []

    def layout(tags: list[str] | None = None, **kwargs: Any):
        seen.append(tags or [])
        return html.Div()

    tester = RouteTester.from_spec({"reports": {"layout": layout}})
    asyncio.run(tester.transition(None, "/reports?tags=eu,us").render())
    asyncio.run(tester.transition(None, "/reports?tags=eu&tags=us").render())
    assert seen == [["eu", "us"], ["eu", "us"]]
    # Both spellings are the same subscribed state, so switching between them renders nothing.
    tester.assert_routes("/reports?tags=eu,us", "/reports?tags=eu&tags=us", expected=[])
    assert Url.parse("/reports").set_param("tags", ["eu", "us"]).to_href() == "/reports?tags=eu,us"


def test_failed_lazy_boundary_renders_its_error_boundary():
    async def endpoint(**kwargs: Any) -> str:
        await asyncio.sleep(0.01)
        return "ok"

    def layout(data: str, **kwargs: Any):
        raise RuntimeError(f"broken:{data}")

    router = DashRouter.from_spec({"orders": {"endpoint": endpoint, "layout": layout, "loading": True, "error": True}})

    plan = router.plan(None, "/orders")
    [skeleton] = asyncio.run(render_patches(router.tree, plan, plan.patches))
    assert ":loading" in str(to_json(skeleton.children))

    [boundary] = asyncio.run(_collect(render_lazy(router.tree, "orders", "/orders")))
    assert "orders:error:broken:ok" in str(to_json(boundary))


def test_missing_children_warning_is_logged_once(caplog: pytest.LogCaptureFixture):
    import logging

    def wrapper_without_children() -> Any:
        return html.Div("no-children")

    tester = RouteTester.from_spec({"orders": {"layout": wrapper_without_children, "sub": {"layout": html.Div("sub")}}})

    with caplog.at_level(logging.WARNING, logger="dash_router"):
        asyncio.run(tester.transition(None, "/orders/sub").render())
        asyncio.run(tester.transition(None, "/orders/sub").render())

    warnings = [r for r in caplog.records if r.name == "dash_router" and r.levelno == logging.WARNING]
    assert len(warnings) == 1
    assert "orders" in warnings[0].getMessage()
    assert "children" in warnings[0].getMessage()


def test_no_missing_children_warning_without_a_child(caplog: pytest.LogCaptureFixture):
    import logging

    def reports() -> Any:
        return html.Div("reports")

    tester = RouteTester.from_spec({"reports": {"layout": reports}})

    with caplog.at_level(logging.WARNING, logger="dash_router"):
        asyncio.run(tester.transition(None, "/reports").render())

    assert [r for r in caplog.records if r.name == "dash_router"] == []


def test_default_error_layout_is_the_last_fallback(tmp_path: Any):
    from dash_router import RouteTree

    pages = tmp_path / "pages"
    pages.mkdir()
    (pages / "reports").mkdir()
    (pages / "reports" / "page.py").write_text("async def page():\n    raise RuntimeError('boom')\n", encoding="utf-8")

    def default_error(exc: BaseException) -> Any:
        return html.Div(f"app-error:{exc}")

    tree = RouteTree.from_folder(pages, default_error_layout=default_error)
    plan = RouteTester(tree).transition(None, "/reports").plan
    updates = asyncio.run(render_patches(tree, plan, plan.patches))
    assert "app-error:boom" in str(to_json(updates[0].children))


def test_history_guard_resumes_push_after_failed_or_settled_navigation():
    import json
    import shutil
    import subprocess
    from pathlib import Path

    if shutil.which("node") is None:
        pytest.skip("node is required for the historyGuard test")

    bundle_path = Path(__file__).resolve().parents[1] / "src" / "dash_router" / "dash_router.min.js"
    script = f"""
    const calls = [];
    let committedHref = "/a";
    let activeCallbacks = [];

    global.self = global;
    global.window = global;
    window.location = {{ pathname: "/a", search: "", hash: "" }};
    window.history = {{
      pushState: (...args) => calls.push(["push", ...args]),
      replaceState: (...args) => calls.push(["replace", ...args]),
    }};
    window.dash_component_api = {{
      getLayout: (id) =>
        id === "dash-router-committed-store"
          ? {{ props: {{ data: {{ href: committedHref }} }} }}
          : undefined,
    }};
    window.dash_stores = [
      {{ getState: () => ({{ callbacks: {{ executing: activeCallbacks }} }}) }},
    ];

    const Module = require("module");
    const origLoad = Module._load;
    Module._load = function(request, parent, isMain) {{
      if (request === "react") return {{}};
      return origLoad.call(this, request, parent, isMain);
    }};
    require({json.dumps(str(bundle_path))});

    // 1. Idle: committed matches location -> push stays push.
    window.history.pushState({{}}, "", "/b");

    // 2. Navigation to /b is in flight -> push of /c becomes replace.
    window.location.pathname = "/b";
    activeCallbacks = [{{ callback: {{ outputs: [{{ id: "dash-router-committed-store", property: "data" }}] }} }}];
    window.history.pushState({{}}, "", "/c");

    // 3. Navigation to /b failed or raised PreventUpdate -> callback left store, committedHref still /a -> push resumes!
    activeCallbacks = [];
    window.history.pushState({{}}, "", "/c");

    console.log(JSON.stringify(calls.map(c => [c[0], c[3]])));
    """
    proc = subprocess.run(["node", "-e", script], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout) == [["push", "/b"], ["replace", "/c"], ["push", "/c"]]
