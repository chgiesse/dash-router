from collections.abc import Callable
from urllib.parse import parse_qsl, urlsplit
from typing import Any

from dash.development.base_component import Component
from flash_router.navigation import url_for
from flash_router.components import RootContainer
from flash_router.router import Router
from flash import Flash, State, callback, Input, Output, get_app, clientside_callback
from quart.ctx import after_this_request
from quart import Response, request
from dash import html, dcc
import json


def redirect(url: str | None = None, params: dict[str, str] | None = None):
    @after_this_request
    async def handle_redirect(_: Response):
        req_data = await request.get_json()
        print(req_data, flush=True)
        update = {RootContainer.ids.dummy: {"href": url}}
        data = {
            "multi": True,
            "response": update
        }
        new_response = Response(json.dumps(data), status=200, mimetype="application/json")
        return new_response

def routing_callback(
    *_args: Any,
    running: list[tuple[Output, Any, Any]] | None = None,
    on_error:  Callable[[Exception], Component]| None = None,
    api_endpoint: str | None = None,
    optional: bool | None = False,
    hidden: bool | None = False,
    **_kwargs: Any,
):
    obsolete_props = [
        "background",
        "interval",
        "progress",
        "progress_default",
        "cancel",
        "manager",
        "cache_args_to_ignore",
        "cache_ignore_triggered"
    ]

    if any(prop in _kwargs for prop in obsolete_props):
        raise ValueError((
            f"One or more obsolete properties used in routing_callback: {', '.join(obsolete_props)}. "
            "Please remove these properties from your callback definition."
        ))

    if any(isinstance(arg, Output) for arg in _args):
        raise ValueError("Outputs are not allowed in routing_callback. Please use the 'running' parameter to specify loading state outputs instead.")

    def decorator(func: Callable[..., Any]):
        @callback(
            *_args,
            State(RootContainer.ids.state_store, "data"),
            running=running,
            on_error=on_error,
            api_endpoint=api_endpoint,
            optional=optional,
            hidden=hidden,
            prevent_initial_call=True,
        )
        async def wrap(*args, **kwargs):

            loading_state = dict((args[-1] or {})) if args else {}
            cb_args = args[:-1] if args else args
            state_query_parameters = dict(loading_state.pop("query_params", {}) or {})
            cb_result = await func(*cb_args, **kwargs)

            @after_this_request
            async def handle_redirect(_: Response):
                app: Flash = get_app()
                router: Router | None = getattr(app, "router", None)
                if router is None:
                    raise RuntimeError("FlashRouter instance not found on app. Ensure that you have initialized Flash with router=FlashRouter.")

                url = cb_result
                if not url:
                    return

                if not isinstance(url, str):
                    raise ValueError("routing_callback callback must return a URL string.")

                parsed = urlsplit(url)
                pathname = parsed.path or "/"
                url_query_parameters = dict(parse_qsl(parsed.query, keep_blank_values=True))
                query_parameters = {**state_query_parameters, **url_query_parameters}

                router_response = await router.resolve_url(pathname, query_parameters, loading_state)
                router_response.response[RootContainer.ids.location] = {"href": url, "refresh": False}
                response = Response(router_response.model_dump_json(), status=200, mimetype="application/json")
                return response
            return
        return wrap
    return decorator


button = html.Button("Click Me - Check redirect", id="test-redirect-button")
url = dcc.Location(id="test-redirect-location", refresh="callback-nav")
second_button = html.Button("Second button", "second-btn")
loader = dcc.Loading(id="loader", type="circle", display="hide")


@routing_callback(
    Input("test-redirect-button", "n_clicks"),
    running=[(Output("loader", "display"), "show", "hide")],
    optional=True
)
async def redirect_callback(_: int):
    url = url_for("projects/[team-id]/files/[--rest]", team_id="alpha", rest=["photos", "folder1"])
    return url

# @callback(Input("second-btn", "n_clicks", allow_optional=True), prevent_initial_call=True)
# async def test2(_: int):
#     print("Executed second callback", flush=True)
#     print("WTF", ctx, flush=True)
#     url = url_for("projects/[team-id]/files/[--rest]", team_id="alpha", rest=["file1", "file2"])
#     return redirect(url)

clientside_callback(
    """
    (href, refresh) => {
        if (href && !refresh) {
            return "callback-nav";
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output(RootContainer.ids.location, "refresh"),
    Input(RootContainer.ids.location, "href"),
    Input(RootContainer.ids.location, "refresh"),
    prevent_initial_call=True
)
