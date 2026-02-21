import re
import json
from pathlib import Path
from typing import TypeAlias, cast
from pydantic import BaseModel


RouteId: TypeAlias = str


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
        "from typing import Literal, overload",
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
        "from .navigation import url_for\n"
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
