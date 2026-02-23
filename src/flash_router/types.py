from collections.abc import Callable, Awaitable, Sequence, Coroutine
from dash.development.base_component import Component
from pydantic import BaseModel
from typing import Literal, Any

BaseType = bool | int | float | str
JSONType = None | BaseType | Sequence["JSONType"] | dict[str, "JSONType"]
QueryParams = dict[str, JSONType]
PathVariables = dict[str, BaseType | Sequence[BaseType]]
ResolveType = Literal["search", "url", "lacy"]
StateType = Literal["lacy", "done", "hidden"]
Endpoint = Callable[..., Awaitable[BaseModel]]
EndpointResults = dict[str, BaseModel | Exception]
Layout = Callable[..., Coroutine[Any, Any, Component]] | Callable[..., Component] | Component
