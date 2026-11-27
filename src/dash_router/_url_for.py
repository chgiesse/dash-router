from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from enum import Enum
from typing import Any, cast
from urllib.parse import quote, urlencode

from pydantic import BaseModel

from .types import REST_TOKENS

type RouteId = str

# Populated by DashRouter when a route tree is built so domain models passed as `params_or_model`
# do not leak unrelated attributes into the query string.
_ROUTE_QUERY_KEYS: dict[str, frozenset[str]] = {}


def register_route_queries(mapping: Mapping[str, frozenset[str]]) -> None:
    """Record the declared query parameter names per `route_id` for `url_for`."""
    _ROUTE_QUERY_KEYS.update(mapping)


def scalar_str(value: Any) -> str:
    if isinstance(value, Enum):
        value = value.value
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _is_collection(value: Any) -> bool:
    return isinstance(value, list | tuple | set | frozenset) or (
        isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray)
    )


def encode_query(items: Mapping[str, Any]) -> str:
    """Serialize query items with comma-separated collections and lowercase booleans."""
    flat: dict[str, str] = {}
    for key, val in items.items():
        if val is None:
            continue
        if _is_collection(val):
            parts = [scalar_str(item) for item in val if item is not None]
            if not parts:
                continue
            flat[key] = ",".join(parts)
        else:
            flat[key] = scalar_str(val)
    if not flat:
        return ""
    return urlencode(flat).replace("%2C", ",")


def _path_param_names(route_id: str) -> set[str]:
    names: set[str] = set()
    for segment in (s for s in route_id.strip("/").split("/") if s):
        match = re.fullmatch(r"\[(.+)\]", segment)
        if not match:
            continue
        raw = match.group(1)
        if raw in REST_TOKENS:
            names.add("rest")
        else:
            names.add(raw)
            names.add(raw.replace("-", "_"))
    return names


def build_route_path(route_id: str, params: Mapping[str, Any]) -> str:
    """Build only the URL pathname from a `route_id` and a parameter mapping."""
    if route_id == "/":
        return "/"
    if REST_TOKENS & params.keys():
        raise ValueError("Catch-all parameter must be passed as 'rest', not '__rest' or '--rest'.")

    resolved: list[str] = []
    for segment in (s for s in route_id.strip("/").split("/") if s):
        if segment.startswith("(") and segment.endswith(")"):
            continue
        match = re.fullmatch(r"\[(.+)\]", segment)
        if not match:
            resolved.append(quote(segment, safe=""))
            continue
        name = match.group(1)
        if name in REST_TOKENS:
            value = params.get("rest")
            items = cast(Sequence[Any], value) if _is_collection(value) else [value]
            resolved.extend(quote(scalar_str(item), safe="") for item in items if item not in (None, ""))
            continue
        value = params.get(name, params.get(name.replace("-", "_")))
        if value is None:
            raise ValueError(f"Missing required path parameter '{name}' for route_id '{route_id}'.")
        resolved.append(quote(scalar_str(value), safe=""))
    return "/" + "/".join(resolved)


def url_for(route_id: RouteId, params_or_model: BaseModel | None = None, **kwargs: object) -> str:
    """Build a URL path (plus query string when given) from a `route_id`, path params, and query params."""
    path_keys = _path_param_names(route_id)
    model_all: dict[str, Any] = params_or_model.model_dump() if params_or_model is not None else {}

    path_params = {**model_all, **kwargs}
    pathname = build_route_path(route_id, path_params)

    query_params: dict[str, Any] = {}
    if params_or_model is not None:
        non_default_dump = params_or_model.model_dump(exclude_defaults=True, exclude_none=True)
        if path_keys & model_all.keys():
            known_query = _ROUTE_QUERY_KEYS.get(route_id)
            if known_query:
                for key in known_query:
                    if key in non_default_dump and key not in path_keys:
                        query_params[key] = non_default_dump[key]
        else:
            for key, val in non_default_dump.items():
                if key not in path_keys:
                    query_params[key] = val

    for key, val in kwargs.items():
        if key not in path_keys:
            query_params[key] = val

    query = encode_query(query_params)
    return f"{pathname}?{query}" if query else pathname
