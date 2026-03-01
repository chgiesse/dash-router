from __future__ import annotations
from collections.abc import Callable, Awaitable, Sequence, Coroutine
from dash.development.base_component import Component
from dash._hooks import HooksManager
from pydantic import BaseModel
from typing import Literal, Any

BaseType = bool | int | float | str
type JSONType = None | BaseType | Sequence[JSONType] | dict[str, JSONType]
QueryParams = dict[str, JSONType]
PathVariables = dict[str, BaseType | Sequence[BaseType]]
ResolveType = Literal["search", "url", "lacy"]
StateType = Literal["lacy", "done", "hidden"]
EndpointResult = BaseModel | Exception | BaseException
EndpointResults = dict[str, EndpointResult]
Endpoint = Callable[..., Awaitable[EndpointResult]]
Layout = Callable[..., Coroutine[Any, Any, Component]] | Callable[..., Component] | Component
ErrorLayout = Layout | HooksManager.HookErrorHandler
