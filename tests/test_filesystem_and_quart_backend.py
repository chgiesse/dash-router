import asyncio
import json
from pathlib import Path
from textwrap import dedent
from typing import Any, cast

import pytest
from dash import Dash, Input, Output, html
from dash._utils import stringify_id
from quart import Quart

from dash_router import (
    ChildContainer,
    DashRouter,
    LazyContainer,
    RootContainer,
    RouteTester,
    RouteTreeValidationError,
    Url,
    navigate,
    url_for,
)
from dash_router.components import LAZY_TYPE


def _write(path: Path, code: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(code).lstrip(), encoding="utf-8")


def test_filesystem_loader_single_import_and_passthrough_slots(tmp_path: Path):
    pages = tmp_path / "pages"

    # Root shell accepting `children`
    _write(
        pages / "page.py",
        """
        from dash import html

        IMPORT_COUNTER = []
        IMPORT_COUNTER.append(1)

        async def layout(children=None):
            return html.Div([html.Nav("Shell"), children], id="app-shell")
        """,
    )

    # Workspace with main routes + a passthrough `(inspector)` slot folder (NO `page.py` inside `(inspector)`, only `default.py` and subroutes!)
    _write(
        pages / "workspace" / "page.py",
        """
        from dash import html
        from dash_router import RouteConfig

        config = RouteConfig(default_child="overview", title="Workspace")

        async def layout(children=None, inspector=None):
            return html.Div([children, inspector], id="workspace-shell")
        """,
    )
    _write(
        pages / "workspace" / "overview" / "page.py",
        """
        from dash import html

        async def layout():
            return html.Div("Overview Main")
        """,
    )
    _write(
        pages / "workspace" / "settings" / "page.py",
        """
        from dash import html

        async def layout():
            return html.Div("Settings Main")
        """,
    )
    _write(
        pages / "workspace" / "(inspector)" / "default.py",
        """
        from dash import html

        async def layout():
            return html.Div("Inspector Default")
        """,
    )
    _write(
        pages / "workspace" / "(inspector)" / "settings" / "page.py",
        """
        from dash import html

        async def layout(data=None):
            return html.Div(f"Inspector Settings: {data}")
        """,
    )
    _write(
        pages / "workspace" / "(inspector)" / "settings" / "api.py",
        """
        async def endpoint():
            return "loaded-from-api"
        """,
    )

    # Organizational empty folder test (`org/reports/page.py` without `org/page.py`)
    _write(
        pages / "org" / "reports" / "page.py",
        """
        from dash import html

        async def layout():
            return html.Div("Org Reports")
        """,
    )

    # Verify relative imports (`from .components import ...`) inside `(slot)` and `[param]` folders!
    _write(
        pages / "workspace" / "items" / "[item_id]" / "components.py",
        """
        def render_item(item_id: str) -> str:
            return f"item:{item_id}"
        """,
    )
    _write(
        pages / "workspace" / "items" / "[item_id]" / "page.py",
        """
        from dash import html
        from .components import render_item

        async def layout(item_id: str):
            return html.Div(render_item(item_id))
        """,
    )
    _write(
        pages / "workspace" / "(inspector)" / "items" / "[item_id]" / "components.py",
        """
        def render_inspector_item(item_id: str) -> str:
            return f"inspector:{item_id}"
        """,
    )
    _write(
        pages / "workspace" / "(inspector)" / "items" / "[item_id]" / "page.py",
        """
        from dash import html
        from .components import render_inspector_item

        async def layout(item_id: str):
            return html.Div(render_inspector_item(item_id))
        """,
    )

    # 1. With `ignore_empty_folders=False`, `org/reports` matches `/org/reports`
    tester_strict = RouteTester.from_folder(pages, ignore_empty_folders=False)
    tester_strict.assert_routes(
        old="/",
        new="/org/reports",
        expected=["org/reports"],
    )

    # 2. With `ignore_empty_folders=True`, `org` is skipped in URL so `/reports` matches!
    tester_ignored = RouteTester.from_folder(pages, ignore_empty_folders=True)
    tester_ignored.assert_routes(
        old="/",
        new="/reports",
        expected=["org/reports"],
    )

    # 3. Verify passthrough parallel slot `(inspector)` works for both `/workspace` (default_child="overview" -> default.py) and `/workspace/settings`
    tester_strict.assert_routes(
        old="/",
        new="/workspace",
        expected=["workspace", "workspace/overview", "workspace/(inspector)"],
        expected_modes={"workspace/(inspector)": "default"},
    )

    res_settings = tester_strict.assert_routes(
        old="/workspace",
        new="/workspace/settings",
        expected=[
            "workspace/settings",
            "workspace/(inspector)",
            "workspace/(inspector)/settings",
        ],
    )
    rendered = asyncio.run(res_settings.render())
    assert "Inspector Settings: loaded-from-api" in str(rendered)

    res_item = tester_strict.assert_routes(
        old="/workspace/settings",
        new="/workspace/items/99",
        expected=[
            "workspace/items/[item_id]",
            "workspace/(inspector)/items/[item_id]",
        ],
    )
    rendered_item = asyncio.run(res_item.render())
    assert "item:99" in str(rendered_item)
    assert "inspector:99" in str(rendered_item)


def test_validation_errors():
    with pytest.raises(RouteTreeValidationError):
        RouteTester.from_spec(
            {
                "static_with_child": {
                    "is_static": True,
                    "nested": {},
                }
            }
        )

    with pytest.raises(RouteTreeValidationError):
        RouteTester.from_spec(
            {
                "bad_default": {
                    "default_child": "missing",
                    "existing": {},
                }
            }
        )


def test_url_for_and_url_builder():
    path = url_for(
        "projects/[team-id]/(sidebar)/files/[__rest]",
        team_id="alpha",
        rest=["2026", "report.csv"],
    )
    assert path == "/projects/alpha/files/2026/report.csv"

    u = Url.parse("/projects/alpha?period=monthly&tag=a")
    u2 = u.to("/projects/beta").update_params(period="daily", tag=None, limit=20)
    assert u2.to_href() == "/projects/beta?period=daily&limit=20"


JSON_HEADERS = {"Content-Type": "application/json"}


def _navigate_key(app: Dash) -> str:
    return next(key for key in app.callback_map if RootContainer.ids.location in str(app.callback_map[key]["inputs"]))


def _navigation_payload(
    output: str,
    pathname: str,
    committed: dict[str, Any] | None,
    mounted: list[Any] | None = None,
) -> dict[str, Any]:
    location = RootContainer.ids.location
    containers = mounted or [RootContainer.ids.container]
    return {
        "output": output,
        "outputs": [
            [{"id": container, "property": "children"} for container in containers],
            {"id": RootContainer.ids.committed_store, "property": "data"},
        ],
        "inputs": [
            {"id": location, "property": "pathname", "value": pathname},
            {"id": location, "property": "search", "value": ""},
        ],
        "changedPropIds": [f"{location}.pathname"],
        "state": [{"id": RootContainer.ids.committed_store, "property": "data", "value": committed}],
    }


def _lazy_payload(output: str, lazy_id: Any, route_json: str) -> dict[str, Any]:
    return {
        "output": output,
        "outputs": {"id": lazy_id, "property": "children"},
        "inputs": [{"id": lazy_id, "property": "data-route", "value": route_json}],
        "changedPropIds": [],
        "state": [{"id": lazy_id, "property": "id", "value": lazy_id}],
    }


def _lazy_containers(node: Any) -> list[dict[str, Any]]:
    """Props of every serialized `LazyContainer` in a rendered tree."""
    if isinstance(node, dict):
        found = [node] if isinstance(node.get("id"), dict) and node["id"].get("type") == LAZY_TYPE else []
        return found + [hit for value in node.values() for hit in _lazy_containers(value)]
    if isinstance(node, list):
        return [hit for item in node for hit in _lazy_containers(item)]
    return []


async def _post_lines(client: Any, payload: dict[str, Any]) -> list[dict[str, Any]]:
    resp = await client.post("/_dash-update-component", data=json.dumps(payload), headers=JSON_HEADERS)
    assert resp.status_code == 200
    body = await resp.get_data(as_text=True)
    return [json.loads(line) for line in body.splitlines() if line.strip()]


def test_quart_dash_backend_streaming_integration(tmp_path: Path):
    pages = tmp_path / "pages"
    _write(
        pages / "tickets" / "page.py",
        """
        from dash import html

        async def layout(children=None):
            return html.Div([html.H2("Tickets Shell"), children], id="tickets-shell")
        """,
    )
    _write(
        pages / "tickets" / "[ticket_id]" / "page.py",
        """
        from dash import html

        async def layout(ticket_id: str, data=None):
            return html.Div(f"Ticket #{ticket_id}: {data}", id="ticket-leaf")
        """,
    )
    _write(
        pages / "tickets" / "[ticket_id]" / "api.py",
        """
        import asyncio

        async def endpoint(ticket_id: str):
            await asyncio.sleep(0.01)
            return f"status-open-{ticket_id}"
        """,
    )
    _write(
        pages / "tickets" / "[ticket_id]" / "loading.py",
        """
        from dash import html

        def layout():
            return html.Div("Loading ticket...", id="ticket-skeleton")
        """,
    )

    quart_server = Quart(__name__)
    app = Dash(__name__, server=cast(Any, quart_server), use_pages=False)
    DashRouter(app, pages_folder=pages)
    app.layout = html.Div([RootContainer()])

    async def _exercise_quart_client() -> None:
        client = quart_server.test_client()

        # 1. GET any nested route serves the SPA index via Quart backend
        resp_index = await client.get("/tickets/42")
        assert resp_index.status_code == 200

        navigate_key = _navigate_key(app)
        lazy_key = next(key for key in app.callback_map if LAZY_TYPE in key)

        # 2. The navigation callback is plain: the shell mounts and the ticket is a LazyContainer skeleton.
        resp_nav = await client.post(
            "/_dash-update-component",
            data=json.dumps(_navigation_payload(navigate_key, "/tickets/42", None)),
            headers=JSON_HEADERS,
        )
        assert resp_nav.status_code == 200
        nav_response = (await resp_nav.get_json())["response"]
        root_children = nav_response[stringify_id(RootContainer.ids.container)]["children"]
        assert "Tickets Shell" in json.dumps(root_children)
        assert "Loading ticket..." in json.dumps(root_children)
        assert "status-open-42" not in json.dumps(root_children)
        assert nav_response[RootContainer.ids.committed_store]["data"] == {
            "url": "/tickets/42",
            "href": "/tickets/42",
            "seq": 1,
            "extra": {},
        }

        # 3. The LazyContainer's `MATCH` streaming callback delivers the resolved ticket, then `{"done": true}`.
        [lazy] = _lazy_containers(root_children)
        assert lazy["id"] == LazyContainer.ids.container("tickets/[ticket_id]@1")
        lines = await _post_lines(client, _lazy_payload(lazy_key, lazy["id"], lazy["data-route"]))
        assert lines[-1] == {"done": True}
        assert len(lines) == 2
        [(lazy_output, lazy_update)] = lines[0]["response"].items()
        assert json.loads(lazy_output) == lazy["id"]
        assert "Ticket #42: status-open-42" in json.dumps(lazy_update["children"])

        # 4. Navigating to the committed URL again is a no-op for the navigation callback.
        repeated = await client.post(
            "/_dash-update-component",
            data=json.dumps(
                _navigation_payload(
                    navigate_key, "/tickets/42", nav_response[RootContainer.ids.committed_store]["data"]
                )
            ),
            headers=JSON_HEADERS,
        )
        assert repeated.status_code == 204

    asyncio.run(_exercise_quart_client())


def test_navigation_diffs_against_the_committed_url_and_navigate_sets_href(tmp_path: Path):
    pages = tmp_path / "pages"
    _write(
        pages / "page.py",
        """
        from dash import html

        def layout(children=None, **_):
            return html.Div([html.H1("Shell"), children])
        """,
    )
    for name in ("a", "b"):
        _write(
            pages / name / "page.py",
            f"""
            from dash import html
            from dash_router import RouteConfig

            config = RouteConfig(title="Page {name.upper()}")
            layout = html.Div("page {name}")
            """,
        )

    quart_server = Quart(__name__)
    app = Dash(__name__, server=cast(Any, quart_server), use_pages=False, suppress_callback_exceptions=True)
    DashRouter(app, pages_folder=pages)
    app.layout = html.Div([RootContainer(), html.Button(id="go"), html.Div(id="msg")])

    @app.callback(Output("msg", "children"), Input("go", "n_clicks"), prevent_initial_call=True)
    async def _go(n_clicks: int | None) -> str:
        navigate(Url.parse("/b").set_param("tab", "x"))
        return "saved"

    async def _post_navigation(payload: dict[str, Any]) -> dict[str, Any] | None:
        """The navigation response's `response` mapping, or `None` when the navigation was a no-op (204)."""
        resp = await quart_server.test_client().post(
            "/_dash-update-component", data=json.dumps(payload), headers=JSON_HEADERS
        )
        if resp.status_code == 204:
            return None
        assert resp.status_code == 200
        return (await resp.get_json())["response"]

    def _navigation(pathname: str, committed: dict[str, Any] | None) -> dict[str, Any]:
        mounted = [RootContainer.ids.container, ChildContainer.ids.container("/")]
        return _navigation_payload(_navigate_key(app), pathname, committed, mounted)

    # `navigate()` only sets the location; the router renders the destination as a navigation.
    clicked = asyncio.run(
        _post_lines(
            quart_server.test_client(),
            {
                "output": "msg.children",
                "outputs": {"id": "msg", "property": "children"},
                "inputs": [{"id": "go", "property": "n_clicks", "value": 1}],
                "changedPropIds": ["go.n_clicks"],
                "state": [],
            },
        )
    )
    assert clicked[0]["sideUpdate"][RootContainer.ids.location] == {"href": "/b?tab=x"}

    # From /a only the shell's `children` is re-rendered, and the next seq + title are committed.
    response = asyncio.run(_post_navigation(_navigation("/b", {"url": "/a", "seq": 4, "extra": {}})))
    assert response is not None
    child_key = stringify_id(ChildContainer.ids.container("/"))
    assert child_key in response
    assert "page b" in json.dumps(response[child_key]["children"])
    assert "Shell" not in json.dumps(response)
    assert response[RootContainer.ids.committed_store]["data"] == {
        "url": "/b",
        "href": "/b",
        "seq": 5,
        "extra": {},
        "title": "Page B",
    }

    # The committed URL itself is a no-op.
    assert asyncio.run(_post_navigation(_navigation("/b", {"url": "/b", "seq": 5, "extra": {}}))) is None


def test_endless_lazy_stream_closes_its_generator_when_the_client_disconnects():
    """The lazy stream's generator is closed once the client goes away, even while it is still yielding."""
    import re

    closed = asyncio.Event()

    async def endless(**_: Any):
        try:
            yield html.Div("live 0")
            while True:
                await asyncio.sleep(0.02)
                yield None
        finally:
            closed.set()

    quart_server = Quart(__name__)
    app = Dash(__name__, server=cast(Any, quart_server), use_pages=False, suppress_callback_exceptions=True)
    DashRouter.from_spec({"live": {"layout": endless}}, app=app)
    app.layout = html.Div([RootContainer()])

    lazy_key = next(key for key in app.callback_map if LAZY_TYPE in key)
    route_json = json.dumps({"node_id": "live", "url": "/live"}, separators=(",", ":"), sort_keys=True)
    body = json.dumps(_lazy_payload(lazy_key, LazyContainer.ids.container("live@1"), route_json)).encode()

    async def _run() -> None:
        client = quart_server.test_client()
        index = await (await client.get("/")).get_data(as_text=True)
        match = re.search(r'"end_id":\s*"([^"]+)"', index)
        assert match, "the page carries a signed end_id"
        url = f"/_dash-update-component?endId={match.group(1)}"
        async with client.request(url, method="POST", headers=JSON_HEADERS) as stream:
            await stream.send(body)
            await stream.send_complete()
            frame = await asyncio.wait_for(stream.receive(), 2)  # the first frame: the generator is running
            assert b"live 0" in frame
            await stream.disconnect()
        await asyncio.wait_for(closed.wait(), 2)

    asyncio.run(_run())
