from collections.abc import AsyncIterator, Awaitable, Callable, Iterator
from typing import Any, Literal

from dash.development.base_component import Component

type ComponentTree = Component | str | int | float | bool | None | list[Any]

type Layout = (
    Component
    | Callable[..., ComponentTree]
    | Callable[..., Awaitable[ComponentTree]]
    | Callable[..., Iterator[ComponentTree]]
    | Callable[..., AsyncIterator[ComponentTree]]
)
type ErrorLayout = Component | Callable[..., ComponentTree] | Callable[..., Awaitable[ComponentTree]]
type Endpoint = Callable[..., Any]

type PathVariables = dict[str, Any]
type QueryParams = dict[str, Any]

type NodeKind = Literal["root", "route", "param", "catch_all", "slot"]
type RenderMode = Literal["page", "default", "empty"]

REST_TOKENS: frozenset[str] = frozenset({"__rest", "--rest"})
