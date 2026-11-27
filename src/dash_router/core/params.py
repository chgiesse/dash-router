import inspect
import types
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Union, get_args, get_origin, get_type_hints
from urllib.parse import parse_qsl, urlsplit

from dash.development.base_component import Component
from pydantic import BaseModel, TypeAdapter

from ..components import ChildContainer, SlotContainer
from ..types import Endpoint, ErrorLayout, Layout

_RESERVED_INJECTED_PARAMS: frozenset[str] = frozenset({"children", "data"})
# Annotations that mark an injected argument (containers, the error of an error layout), not a query input.
_INJECTED_TYPES: tuple[type[Any], ...] = (Component, ChildContainer, SlotContainer, BaseException)
_EMPTY = inspect.Parameter.empty


def _unwrap_optional(tp: Any) -> Any:
    """`T | None` -> `T`; other annotations unchanged."""
    if get_origin(tp) in (Union, types.UnionType):
        args = [a for a in get_args(tp) if a is not type(None)]
        if len(args) == 1:
            return args[0]
    return tp


def _is_collection_type(tp: Any) -> bool:
    inner = _unwrap_optional(tp)
    return (get_origin(inner) or inner) in (list, tuple, set, frozenset)


def _classify_param_type(tp: Any) -> str:
    if tp is _EMPTY or tp is Any:
        return "untyped"
    inner = _unwrap_optional(tp)
    if inspect.isclass(inner):
        if issubclass(inner, _INJECTED_TYPES):
            return "skip"
        if issubclass(inner, BaseModel):
            return "pydantic"
        if issubclass(inner, Enum) or inner in (str, int, float, bool, list, tuple, set):
            return "scalar"
    if get_origin(inner) is not None or getattr(tp, "__module__", None) in ("builtins", "typing", "types"):
        return "scalar"
    return "skip"


@dataclass
class _QueryInputs:
    """Accumulates the query inputs declared by one signature."""

    names: set[str] = field(default_factory=set)
    collections: set[str] = field(default_factory=set)
    defaults: dict[str, Any] = field(default_factory=dict)
    adapters: dict[str, TypeAdapter[Any]] = field(default_factory=dict)
    models: dict[str, type[BaseModel]] = field(default_factory=dict)
    types: dict[str, Any] = field(default_factory=dict)

    def add(self, name: str, tp: Any, default: Any = _EMPTY) -> None:
        self.names.add(name)
        if default is not _EMPTY:
            self.defaults[name] = default
        if tp is _EMPTY or tp is None:
            return
        self.types[name] = tp
        if _is_collection_type(tp):
            self.collections.add(name)
        if name not in self.adapters:
            try:
                self.adapters[name] = TypeAdapter(tp)
            except Exception:
                pass

    def add_model(self, param_name: str, model: type[BaseModel]) -> None:
        """A Pydantic model argument subscribes to each of its fields as a query input."""
        self.models[param_name] = model
        for name, info in model.model_fields.items():
            default: Any = _EMPTY
            if info.default_factory is not None:
                try:
                    default = info.default_factory()  # type: ignore[call-arg]
                except Exception:
                    pass
            elif not info.is_required():
                default = info.default
            self.add(name, info.annotation, default)


@dataclass(frozen=True)
class FunctionSignatureInfo:
    is_callable: bool = False
    is_coroutine: bool = False
    is_generator: bool = False
    is_async_generator: bool = False
    accepts_var_kwargs: bool = False
    param_names: frozenset[str] = field(default_factory=frozenset)
    required_params: frozenset[str] = field(default_factory=frozenset)
    accepts_children: bool = False
    query_inputs: frozenset[str] = field(default_factory=frozenset)
    collection_inputs: frozenset[str] = field(default_factory=frozenset)
    input_defaults: dict[str, Any] = field(default_factory=dict)
    pydantic_params: dict[str, type[BaseModel]] = field(default_factory=dict)
    type_adapters: dict[str, TypeAdapter[Any]] = field(default_factory=dict)
    param_types: dict[str, Any] = field(default_factory=dict)

    @property
    def is_streaming(self) -> bool:
        return self.is_generator or self.is_async_generator

    @classmethod
    def analyze(
        cls,
        obj: Layout | ErrorLayout | Endpoint | None,
        slot_names: set[str] | None = None,
    ) -> "FunctionSignatureInfo":
        if obj is None or isinstance(obj, Component) or not callable(obj):
            return cls()

        sig = inspect.signature(obj)
        try:
            hints = get_type_hints(obj)
        except Exception:
            hints = {}

        injected = _RESERVED_INJECTED_PARAMS | (slot_names or set())
        params = [p for p in sig.parameters.values() if p.kind not in (p.VAR_POSITIONAL, p.VAR_KEYWORD)]
        inputs = _QueryInputs()
        for param in params:
            if param.name in injected:
                continue
            tp = hints.get(param.name, param.annotation)
            match _classify_param_type(tp):
                case "pydantic":
                    inputs.add_model(param.name, _unwrap_optional(tp))
                case "scalar":
                    inputs.add(param.name, tp, param.default)
                case "untyped":
                    inputs.add(param.name, _EMPTY, param.default)

        param_names = frozenset(p.name for p in params)
        return cls(
            is_callable=True,
            is_coroutine=inspect.iscoroutinefunction(obj),
            is_generator=inspect.isgeneratorfunction(obj),
            is_async_generator=inspect.isasyncgenfunction(obj),
            accepts_var_kwargs=any(p.kind == p.VAR_KEYWORD for p in sig.parameters.values()),
            param_names=param_names,
            required_params=frozenset(p.name for p in params if p.default is _EMPTY),
            accepts_children="children" in param_names,
            query_inputs=frozenset(inputs.names),
            collection_inputs=frozenset(inputs.collections),
            input_defaults=inputs.defaults,
            pydantic_params=inputs.models,
            type_adapters=inputs.adapters,
            param_types=inputs.types,
        )


def parse_query(query: str) -> dict[str, Any]:
    """`a=1&b=2&b=3` -> `{"a": "1", "b": ["2", "3"]}` (repeated keys become lists)."""
    grouped: dict[str, list[str]] = {}
    for key, val in parse_qsl(query, keep_blank_values=True):
        grouped.setdefault(key, []).append(val)
    return {key: vals[0] if len(vals) == 1 else vals for key, vals in grouped.items()}


def parse_url(url: str) -> tuple[str, dict[str, Any]]:
    """Split a URL or path+search string into `(normalized_pathname, raw_query_dict)`."""
    if not url:
        return "/", {}
    split = urlsplit(url)
    path = "/" + split.path.strip("/") if split.path else "/"
    return path, parse_query(split.query)


def as_list(value: Any) -> list[Any]:
    """Raw query value of a collection input -> list.

    Lists are written comma separated (`?status=open,closed`, the format of `UrlParam`);
    repeated keys (`?status=open&status=closed`) are accepted too.
    """
    if isinstance(value, list | tuple | set | frozenset):
        return list(value)
    if isinstance(value, str):
        text = value.strip()
        return [part.strip() for part in text.split(",")] if text else []
    return [value]


def build_call_kwargs(
    sig_info: FunctionSignatureInfo,
    raw_vars: dict[str, Any],
    injected: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Prepare coerced keyword arguments (including Pydantic models) for `sig_info`."""
    merged: dict[str, Any] = dict(raw_vars)

    for param_name, model_cls in sig_info.pydantic_params.items():
        if isinstance(merged.get(param_name), model_cls):
            continue
        payload = {
            name: as_list(merged[name]) if _is_collection_type(info.annotation) else merged[name]
            for name, info in model_cls.model_fields.items()
            if merged.get(name) is not None
        }
        merged[param_name] = model_cls.model_validate(payload)

    for param_name, adapter in sig_info.type_adapters.items():
        val = merged.get(param_name)
        if val is None:
            continue
        if param_name in sig_info.collection_inputs:
            val = as_list(val)
        merged[param_name] = adapter.validate_python(val)

    if injected:
        merged.update(injected)
    if sig_info.accepts_var_kwargs:
        return merged
    return {k: v for k, v in merged.items() if k in sig_info.param_names}


def start_callable(
    target: Layout | ErrorLayout | Endpoint,
    sig_info: FunctionSignatureInfo,
    *pos_args: Any,
    raw_vars: dict[str, Any] | None = None,
    injected: dict[str, Any] | None = None,
) -> Any:
    """Invoke `target` with coerced arguments without awaiting or draining generators."""
    if not sig_info.is_callable or not callable(target):
        return target
    return target(*pos_args, **build_call_kwargs(sig_info, raw_vars or {}, injected))


async def invoke(
    target: Layout | ErrorLayout | Endpoint,
    sig_info: FunctionSignatureInfo,
    *pos_args: Any,
    raw_vars: dict[str, Any] | None = None,
    injected: dict[str, Any] | None = None,
) -> Any:
    """Call `target` and resolve its result. A generator resolves to its first non-`None` item."""
    result = start_callable(target, sig_info, *pos_args, raw_vars=raw_vars, injected=injected)
    if inspect.isasyncgen(result):
        try:
            async for item in result:
                if item is not None:
                    return item
        finally:
            await result.aclose()
        return None
    if inspect.isgenerator(result):
        try:
            return next((item for item in result if item is not None), None)
        finally:
            result.close()
    if inspect.isawaitable(result):
        return await result
    return result
