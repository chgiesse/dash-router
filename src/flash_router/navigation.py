import json
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any, Literal, TypeAlias, cast
from urllib.parse import parse_qs, parse_qsl, urlencode, urlsplit

import quart
from dash.development.base_component import Component
from flash import Flash, Output, State, callback, get_app
from pydantic import BaseModel, Field
from quart import Response
from quart.ctx import after_this_request

from flash_router.core.routing import RoutingContext

from .components import RootContainer

RouteId: TypeAlias = str

def get_current_url(strict: bool = False) -> "Url":
    if strict and not quart.request:
        raise RuntimeError("No request context available")

    if not quart.request:
        return Url(pathname="/", search={})

    headers = quart.request.headers
    referer = headers.get("Referer")
    if not referer:
        return Url(pathname=quart.request.path or "/", search={})

    parsed = urlsplit(referer)
    parsed_qs = parse_qs(parsed.query)
    search = {key: values[0] if values else "" for key, values in parsed_qs.items()}
    return Url(
        pathname=parsed.path or "/",
        search=search,
    )


class Url(BaseModel):
    pathname: str = Field(default_factory=lambda: get_current_url(strict=True).pathname)
    search: dict[str, Any] = Field(default_factory=dict)
    update_type: Literal["href", "search"] = "href"

    @classmethod
    def parse(cls, href: str) -> "Url":
        parsed = urlsplit(href)
        return cls(
            pathname=parsed.path or "/",
            search=dict(parse_qsl(parsed.query, keep_blank_values=True)),
            update_type="href",
        )

    def to(self, pathname: str) -> "Url":
        return self.model_copy(update={"pathname": pathname, "update_type": "href"})

    def set_param(self, key: str, value: Any) -> "Url":
        """Return a new Url with a single query parameter set or replaced."""
        return self.model_copy(update={"search": {**self.search, key: value}})

    def remove_param(self, key: str) -> "Url":
        """Return a new Url with a single query parameter removed (no-op if absent)."""
        return self.model_copy(update={"search": {k: v for k, v in self.search.items() if k != key}})

    def update_params(self, **query: Any) -> "Url":
        """Return a new Url with multiple query parameters merged in.

        Pass ``None`` as a value to remove that key.
        """
        return self.model_copy(update={
            "search": {
                **{k: v for k, v in self.search.items() if k not in query or query[k] is not None},
                **{k: v for k, v in query.items() if v is not None},
            },
            "update_type": "href",
        })

    def clear_query(self) -> "Url":
        return self.model_copy(update={"search": {}, "update_type": "search"})

    def update(self, update_type: Literal["href", "search"]) -> "Url":
        """Return a new Url with the update_type explicitly set."""
        return self.model_copy(update={"update_type": update_type})

    def to_href(self) -> str:
        pathname = self.pathname or "/"
        if not self.search:
            return pathname
        return f"{pathname}?{urlencode(self.search, doseq=True)}"


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
            prev_qs = loading_state.pop("query_params", {})
            _ = loading_state.pop("is_redirect")
            cb_result = await func(*cb_args, **kwargs)

            @after_this_request
            async def handle_redirect(_: Response):
                app: Flash = get_app()
                router = getattr(app, "router", None)
                if router is None:
                    raise RuntimeError("FlashRouter instance not found on app. Ensure that you have initialized Flash with router=FlashRouter.")

                if not cb_result:
                    return

                if not isinstance(cb_result, Url):
                    raise ValueError(
                        "routing_callback callback must return a Url class."
                    )

                routing_ctx = RoutingContext.from_request(
                    pathname=cb_result.pathname,
                    curr_qs=cb_result.search,
                    loading_state_dict=loading_state,
                    prev_qs=prev_qs,
                    resolve_type="url",
                )

                if cb_result.update_type == "search":
                    routing_ctx.resolve_type = "search"
                    router_response = await router.resolve_search(
                        ctx=routing_ctx,
                        is_redirect=True,
                    )
                else:
                    router_response = await router.resolve_url(
                        ctx=routing_ctx,
                        is_redirect=True,
                    )

                router_response.response[RootContainer.ids.location] = {
                    "href": cb_result.to_href(),
                    "update_type": cb_result.update_type,
                }
                response = Response(router_response.model_dump_json(), status=200, mimetype="application/json")
                return response
            return
        return wrap
    return decorator


def url_for(
    route_id: RouteId,
    params_or_model: BaseModel | None = None,
    **kwargs: object,
) -> str:
    """Build a URL path from a route node id and path parameters.

    The function resolves dynamic route segments like ``[team-id]`` from either:
    - ``params_or_model`` (a Pydantic model), and/or
    - keyword arguments.

    For catch-all segments (``[__rest]`` / ``[--rest]``), pass ``rest`` as
    either a list/tuple of segments or a scalar.

    During development mode, the router generates type stubs that provide
    route-id completion and route-specific keyword argument completion in IDEs.
    In production mode, these stubs are not generated.

    Examples:
        url_for("projects/[team-id]/files", team_id="alpha")
        --> "/projects/alpha/files"

        url_for(
            "projects/[team-id]/files/[--rest]",
            team_id="alpha",
            rest=["file1", "file2"],
        )
        --> "/projects/alpha/files/file1/file2"
    """
    if route_id == "/":
        return "/"

    params = _model_to_params(params_or_model)
    params.update(kwargs)

    if "__rest" in params or "--rest" in params:
        raise ValueError(
            "Catch-all parameter must be passed as 'rest', not '__rest' or '--rest'."
        )

    resolved_segments: list[str] = []
    path_segments = [segment for segment in route_id.strip("/").split("/") if segment]

    for segment in path_segments:
        if segment.startswith("(") and segment.endswith(")"):
            continue

        match = re.fullmatch(r"\[(.+)\]", segment)
        if not match:
            resolved_segments.append(segment)
            continue

        param_name = match.group(1)
        value = _extract_param_value(param_name, params)

        if param_name in {"__rest", "--rest"}:
            if value in (None, ""):
                continue

            if isinstance(value, (list, tuple)):
                values = cast(list[object] | tuple[object, ...], value)
                resolved_segments.extend(
                    str(item) for item in values if item not in (None, "")
                )
                continue

            resolved_segments.append(str(value))
            continue

        if value is None:
            raise ValueError(
                f"Missing required path parameter '{param_name}' for route_id '{route_id}'"
            )

        resolved_segments.append(str(value))

    return "/" + "/".join(resolved_segments)


def _canonicalize_route_ids(route_ids: list[str]) -> list[str]:
    canonical_route_ids: list[str] = []

    for route_id in route_ids:
        if route_id.endswith(")"):
            continue

        canonical_route_ids.append(route_id)

    return canonical_route_ids


def _to_python_param_name(route_param: str) -> str | None:
    candidate = route_param.replace("-", "_")
    if not candidate.isidentifier():
        return None
    return candidate


def _build_navigation_stub(route_ids: list[str]) -> str:
    lines = [
        "from typing import Any, Literal, overload",
        "from pydantic import BaseModel",
        "",
        "from ._route_types import RouteId",
        "",
    ]

    for route_id in route_ids:
        route_literal = json.dumps(route_id)
        route_params: list[str] = []
        for segment in route_id.split("/"):
            if segment.startswith("[") and segment.endswith("]"):
                route_params.append(segment[1:-1])
        kwargs: list[tuple[str, str]] = []
        seen_params: set[str] = set()
        has_invalid_param = False

        for raw_param in route_params:
            param_name = _to_python_param_name(raw_param)
            if not param_name or param_name in seen_params:
                has_invalid_param = True
                break

            seen_params.add(param_name)
            if raw_param in {"__rest", "--rest"}:
                param_name = "rest"
                param_type = "object | list[object] | tuple[object, ...]"
            else:
                param_type = "object"

            kwargs.append((param_name, param_type))

        lines.append("@overload")
        if has_invalid_param:
            lines.append(
                "def url_for("
                + f"route_id: Literal[{route_literal}], "
                + "params_or_model: BaseModel | None = ..., "
                + "**kwargs: object"
                + ") -> str: ..."
            )
            lines.append("")
            continue

        if kwargs:
            kwarg_sig = ", ".join(f"{name}: {typ}" for name, typ in kwargs)
            lines.append(
                "def url_for("
                + f"route_id: Literal[{route_literal}], "
                + "params_or_model: BaseModel | None = ..., *, "
                + f"{kwarg_sig}"
                + ") -> str: ..."
            )
        else:
            lines.append(
                "def url_for("
                + f"route_id: Literal[{route_literal}], "
                + "params_or_model: BaseModel | None = ..."
                + ") -> str: ..."
            )
        lines.append("")

    lines.append(
        "def url_for(route_id: RouteId, params_or_model: BaseModel | None = ..., **kwargs: object) -> str: ..."
    )
    return "\n".join(lines) + "\n"


def generate_navigation_typing(route_ids: list[str]) -> None:
    canonical_route_ids = _canonicalize_route_ids(route_ids)

    if canonical_route_ids:
        literals = ", ".join(
            json.dumps(route_id) for route_id in canonical_route_ids
        )
        content = f"from typing import Literal\n\nRouteId = Literal[{literals}]\n"
    else:
        content = "from typing import Literal\n\nRouteId = Literal[\"\"]\n"

    stub_package_path = Path.cwd() / ".flash_router_typing" / "flash_router"
    stub_package_path.mkdir(parents=True, exist_ok=True)

    route_types_stub_path = stub_package_path / "_route_types.pyi"
    _ = route_types_stub_path.write_text(content, encoding="utf-8")

    init_stub_path = stub_package_path / "__init__.pyi"
    init_stub = (
        "from ._route_types import RouteId\n"
        "from .navigation import Url, get_current_url, url_for\n"
    )
    _ = init_stub_path.write_text(init_stub, encoding="utf-8")

    navigation_stub_path = stub_package_path / "navigation.pyi"
    navigation_stub = _build_navigation_stub(canonical_route_ids)
    _ = navigation_stub_path.write_text(navigation_stub, encoding="utf-8")


def _model_to_params(params_or_model: BaseModel | None) -> dict[str, object]:
    if params_or_model is None:
        return {}

    return params_or_model.model_dump()


def _extract_param_value(name: str, params: dict[str, object]) -> object | None:
    if name in {"__rest", "--rest"}:
        if "__rest" in params or "--rest" in params:
            raise ValueError(
                "Catch-all parameter must be passed as 'rest', not '__rest' or '--rest'."
            )
        return params.get("rest")

    if name in params:
        return params[name]

    alt_name = name.replace("-", "_")
    if alt_name in params:
        return params[alt_name]

    return None
