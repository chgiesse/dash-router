from __future__ import annotations

import importlib.util
import inspect
import json
import keyword
import os
import re
import sys
import tempfile
import types
from collections.abc import Iterable, Sequence
from collections.abc import Set as AbstractSet
from contextlib import suppress
from enum import Enum
from pathlib import Path
from typing import Annotated, Any, Literal, Union, get_args, get_origin
from urllib.parse import quote, urlsplit

from dash import callback_context, set_props
from pydantic import BaseModel, Field

from ._url_for import RouteId as RouteId
from ._url_for import encode_query
from ._url_for import url_for as url_for
from .components import RootContainer
from .core.matcher import match_url
from .core.params import FunctionSignatureInfo, parse_query
from .core.tree import RouteNode, RouteTree
from .types import REST_TOKENS, RenderMode

_EMPTY = inspect.Parameter.empty
_RESERVED_STUB_NAMES = frozenset({"Any", "Literal", "Never", "Protocol", "RouteId", "Sequence", "overload", "url_for"})


_UNSAFE_PATH_CHARS = re.compile(r"[^A-Za-z0-9\-._~/:@!$&'()*+,;=%]|%(?![0-9A-Fa-f]{2})")


class Url(BaseModel):
    """Immutable URL (path + query). Lists are written comma separated, like `UrlParam` does."""

    pathname: str = "/"
    search: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def parse(cls, href: str) -> Url:
        parts = urlsplit(href)
        return cls(pathname=parts.path or "/", search=parse_query(parts.query))

    def to(self, pathname: str) -> Url:
        return self.model_copy(update={"pathname": pathname or "/"})

    def set_param(self, key: str, value: Any) -> Url:
        return self.update_params(**{key: value})

    def remove_param(self, key: str) -> Url:
        return self.update_params(**{key: None})

    def update_params(self, **query: Any) -> Url:
        """Set several parameters at once; `None` removes one."""
        merged = {**self.search, **query}
        return self.model_copy(update={"search": {k: v for k, v in merged.items() if v is not None}})

    def clear_query(self) -> Url:
        return self.model_copy(update={"search": {}})

    def to_href(self) -> str:
        pathname = _UNSAFE_PATH_CHARS.sub(lambda m: quote(m.group(0), safe=""), "/" + self.pathname.lstrip("/"))
        query = encode_query(self.search)
        return f"{pathname}?{query}" if query else pathname

    def __str__(self) -> str:
        return self.to_href()


def _is_asset_path(path: str) -> bool:
    """Dash asset / stream-worker script URL: what a streaming callback's worker sends as `Referer`."""
    return path.endswith((".js", ".css", ".map")) or path.startswith("/_dash-")


def get_current_url(strict: bool = False) -> Url:
    """URL of the page that sent the current callback, from its `Referer` header.

    Inside streaming callbacks the browser sends the stream worker's script as `Referer`; take
    `State(RootContainer.ids.location, "href")` as an input there instead. Without a page URL
    this returns `/`, or raises `RuntimeError` when `strict`.
    """
    try:
        headers = {key.lower(): value for key, value in (callback_context.headers or {}).items()}
    except Exception:
        headers = {}
    referer = headers.get("referer")
    if referer and not _is_asset_path(urlsplit(referer).path):
        return Url.parse(referer)
    if strict:
        raise RuntimeError("No callback request with a page Referer available.")
    return Url()


def navigate(url: str | Url) -> None:
    """Navigate from any Dash callback: the router renders the destination as a normal navigation."""
    set_props(RootContainer.ids.location, {"href": str(url)})


# ─── STUB GENERATION ─────────────────────────────────────────────────────────


def default_stubs_dir(pages_folder: Path) -> Path:
    """Resolve the default `typings/` directory for `pages_folder`.

    Walks up from `pages_folder.parent` looking for `pyrightconfig.json` or `pyproject.toml`,
    stopping before crossing an `examples`/`tests`/`.git` boundary so example apps and test
    trees keep their stubs self-contained.
    """
    base = pages_folder.resolve().parent
    for cur in (base, *base.parents):
        if (cur / "pyrightconfig.json").is_file() or (cur / "pyproject.toml").is_file():
            return cur / "typings"
        if cur.name in ("examples", "example", "tests", "test") or (cur / ".git").exists():
            break
    return base / "typings"


def collect_route_query_keys(
    tree: RouteTree,
    excluded_inputs: AbstractSet[str] = frozenset(),
) -> dict[str, frozenset[str]]:
    """Map each `route_id` to its active query parameter names across ancestors, slots, and default children."""
    result: dict[str, frozenset[str]] = {}
    for route_id in tree.nodes:
        if route_id.endswith(")"):
            continue
        info = _collect_route_inputs(tree, route_id, excluded_inputs=excluded_inputs)
        result[route_id] = frozenset(info.query_types)
    return result


def generate_navigation_typing(
    source: RouteTree | Sequence[str],
    output_dir: Path | None = None,
    *,
    excluded_inputs: AbstractSet[str] = frozenset(),
    project_root: Path | None = None,
) -> Path:
    """Write PEP 561 partial stubs (`typings/dash_router-stubs/`) typing `RouteId` and `url_for`."""
    typings_root = (output_dir or (Path.cwd() / "typings")).resolve()
    stub_pkg = typings_root / "dash_router-stubs"
    stub_pkg.mkdir(parents=True, exist_ok=True)

    root_for_imports = (project_root or typings_root.parent).resolve()
    stub_content = _render_url_for_stub(source, root_for_imports, excluded_inputs=excluded_inputs)

    _write_if_changed(stub_pkg / ".gitignore", "*\n")
    _write_if_changed(stub_pkg / "py.typed", "partial\n")
    _write_if_changed(stub_pkg / "_url_for.pyi", stub_content)
    for extra_pyi in stub_pkg.glob("*.pyi"):
        if extra_pyi.name != "_url_for.pyi":
            with suppress(OSError):
                extra_pyi.unlink()
    return stub_pkg


def _write_if_changed(path: Path, content: str) -> None:
    if path.is_file():
        try:
            if path.read_text(encoding="utf-8") == content:
                return
        except OSError:
            pass
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
        os.replace(tmp_path, path)
    except BaseException:
        with suppress(OSError):
            tmp_path.unlink()
        raise


class _RouteInputs:
    __slots__ = ("path_params", "rest_type", "has_rest", "query_types", "query_models", "invalid_path", "has_invalid_query")

    def __init__(self) -> None:
        self.path_params: list[tuple[str, Any]] = []
        self.rest_type: Any = _EMPTY
        self.has_rest: bool = False
        self.query_types: dict[str, Any] = {}
        self.query_models: list[type[BaseModel]] = []
        self.invalid_path: bool = False
        self.has_invalid_query: bool = False


def _active_route_nodes(tree: RouteTree, node_id: str) -> tuple[list[RouteNode], list[tuple[RouteNode, RenderMode, bool]]]:
    node = tree.nodes[node_id]
    ancestors: list[RouteNode] = []
    cur: RouteNode | None = node
    while cur is not None:
        ancestors.append(cur)
        cur = tree.nodes.get(cur.parent_id) if cur.parent_id is not None else None
    ancestors.reverse()

    if node.is_static:
        segs = [
            "a" if p[1:-1] in REST_TOKENS else ("1" if p.startswith("[") and p.endswith("]") else p)
            for p in node_id.split("/")
            if p
        ]
    else:
        segs = []
        for anc in ancestors:
            if anc.kind in ("root", "slot"):
                continue
            if anc.kind == "route":
                segs.extend(anc.route_segments)
            elif anc.kind == "param":
                segs.extend((*anc.route_segments, "1"))
            elif anc.kind == "catch_all":
                segs.extend((*anc.route_segments, "a"))

    synthetic_url = "/" + "/".join(segs)
    matched_tree = match_url(tree, synthetic_url)
    active: list[tuple[RouteNode, RenderMode, bool]] = []
    seen_ids: set[str] = set()
    if matched_tree is not None:
        for matched in matched_tree.root.walk():
            if matched.mode == "empty":
                continue
            seen_ids.add(matched.node_id)
            active.append((tree.nodes[matched.node_id], matched.mode, matched.omitted))
    for anc in reversed(ancestors):
        if anc.node_id not in seen_ids:
            seen_ids.add(anc.node_id)
            active.append((anc, "page", False))
    return ancestors, active


def _node_sigs(node: RouteNode) -> tuple[FunctionSignatureInfo, ...]:
    return (
        node.layout_sig,
        node.endpoint_sig,
        node.default_sig,
        node.loading_sig,
        node.error_sig,
        node.title_sig,
    )


def _find_param_type(
    param_name: str,
    ancestors: list[RouteNode],
    active: list[tuple[RouteNode, RenderMode, bool]],
) -> Any:
    owners = [a for a in ancestors if a.kind in ("param", "catch_all") and a.name == param_name]
    ordered_nodes = [*owners, *(n for n, _, _ in active if n not in owners)]
    for node in ordered_nodes:
        for sig in _node_sigs(node):
            tp = sig.param_types.get(param_name, _EMPTY)
            if tp is not _EMPTY and tp is not Any:
                return tp
    return _EMPTY


def _collect_route_inputs(
    tree: RouteTree,
    node_id: str,
    *,
    excluded_inputs: AbstractSet[str] = frozenset(),
) -> _RouteInputs:
    ancestors, active = _active_route_nodes(tree, node_id)
    info = _RouteInputs()

    seen_path: set[str] = set()
    for raw in (seg[1:-1] for seg in node_id.split("/") if seg.startswith("[") and seg.endswith("]")):
        name = "rest" if raw in REST_TOKENS else raw.replace("-", "_")
        if not name.isidentifier() or keyword.iskeyword(name) or name in ("route_id", "params_or_model") or name in seen_path:
            info.invalid_path = True
            break
        seen_path.add(name)
        tp = _find_param_type(name, ancestors, active)
        if raw in REST_TOKENS:
            info.has_rest = True
            info.rest_type = tp
        else:
            info.path_params.append((name, tp))

    seen_models: set[type[BaseModel]] = set()
    for anode, mode, omitted in active:
        if mode == "default":
            sigs = (anode.default_sig,) if anode.default_layout is not None else (anode.layout_sig,)
        else:
            sigs = (anode.layout_sig, anode.endpoint_sig) if not omitted else (anode.layout_sig,)
        allowed = anode.query.names - excluded_inputs - seen_path

        for sig in sigs:
            for model_cls in sig.pydantic_params.values():
                if set(model_cls.model_fields) & allowed:
                    if model_cls not in seen_models:
                        seen_models.add(model_cls)
                        info.query_models.append(model_cls)
                    for fname in model_cls.model_fields:
                        if fname in allowed and fname not in info.query_types:
                            info.query_types[fname] = sig.param_types.get(fname, _EMPTY)
            for qname in sig.query_inputs:
                if qname not in allowed:
                    continue
                tp = sig.param_types.get(qname, _EMPTY)
                if qname not in info.query_types or (info.query_types[qname] is _EMPTY and tp is not _EMPTY):
                    info.query_types[qname] = tp

        for extra_name in sorted(allowed):
            if extra_name not in info.query_types:
                info.query_types[extra_name] = _EMPTY

    for qname in list(info.query_types):
        if not qname.isidentifier() or keyword.iskeyword(qname) or qname in ("route_id", "params_or_model"):
            info.query_types.pop(qname)
            info.has_invalid_query = True

    return info


def _collect_basic_route_inputs(route_id: str) -> _RouteInputs:
    info = _RouteInputs()
    seen: set[str] = set()
    for raw in (seg[1:-1] for seg in route_id.split("/") if seg.startswith("[") and seg.endswith("]")):
        name = "rest" if raw in REST_TOKENS else raw.replace("-", "_")
        if not name.isidentifier() or keyword.iskeyword(name) or name in ("route_id", "params_or_model") or name in seen:
            info.invalid_path = True
            break
        seen.add(name)
        if raw in REST_TOKENS:
            info.has_rest = True
        else:
            info.path_params.append((name, _EMPTY))
    return info


def _unwrap_optional(tp: Any) -> Any:
    if get_origin(tp) in (Union, types.UnionType):
        args = [a for a in get_args(tp) if a is not type(None)]
        if len(args) == 1:
            return args[0]
        if len(args) < len(get_args(tp)):
            res: Any = args[0]
            for a in args[1:]:
                res = res | a
            return res
    return tp


def _is_stdlib_or_site_path(file_path: Path) -> bool:
    parts = file_path.parts
    if "site-packages" in parts or "dist-packages" in parts:
        return True
    for prefix in {Path(sys.prefix).resolve(), Path(sys.base_prefix).resolve()}:
        if file_path.is_relative_to(prefix):
            return True
    return False


class _StubTypeRenderer:
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.typing_imports: set[str] = set()
        self.abc_imports: set[str] = set()
        self.imports: dict[str, dict[str, str]] = {}
        self.used_names: set[str] = set(_RESERVED_STUB_NAMES)
        self.synthetic_models: dict[type[BaseModel], str] = {}
        self._model_defs: list[list[str]] = []
        self._path_protocols: dict[tuple[tuple[str, str], ...], str] = {}
        self._path_protocol_defs: list[list[str]] = []
        self._resolving_models: set[type[BaseModel]] = set()

    def _import_symbol(self, mod_name: str, symbol: str) -> str:
        mod_map = self.imports.setdefault(mod_name, {})
        if symbol in mod_map:
            return mod_map[symbol]
        alias = symbol
        counter = 2
        while alias in self.used_names:
            alias = f"{symbol}_{counter}"
            counter += 1
        self.used_names.add(alias)
        mod_map[symbol] = alias
        return alias

    def _importable_module(self, cls: type[Any]) -> str | None:
        mod_name = getattr(cls, "__module__", None)
        qualname = getattr(cls, "__qualname__", getattr(cls, "__name__", ""))
        if not mod_name or mod_name == "__main__" or "<locals>" in qualname or "." in qualname:
            return None
        if mod_name == "builtins":
            return "builtins"
        mod = sys.modules.get(mod_name)
        mod_file = getattr(mod, "__file__", None) if mod is not None else None
        if mod_file:
            resolved = Path(mod_file).resolve()
            if not _is_stdlib_or_site_path(resolved):
                roots = [self.project_root]
                for entry in sys.path:
                    if entry:
                        with suppress(OSError):
                            p = Path(entry).resolve()
                            if p not in roots and p.is_dir():
                                roots.append(p)
                for root in roots:
                    if resolved.is_relative_to(root):
                        rel = resolved.relative_to(root)
                        parts = rel.parent.parts if rel.name == "__init__.py" else (*rel.parent.parts, rel.stem)
                        if parts and all(part.isidentifier() and not keyword.iskeyword(part) for part in parts):
                            return ".".join(parts)
                return None
        try:
            spec = importlib.util.find_spec(mod_name)
        except (ValueError, ImportError):
            return None
        if spec is None:
            return None
        return mod_name

    def _ensure_synthetic_model(self, model_cls: type[BaseModel]) -> str:
        if model_cls in self.synthetic_models:
            return self.synthetic_models[model_cls]
        base_name = re.sub(r"\W+", "_", model_cls.__name__) or "Model"
        name = f"_QueryModel_{base_name}"
        counter = 2
        while name in self.used_names:
            name = f"_QueryModel_{base_name}_{counter}"
            counter += 1
        self.used_names.add(name)
        self.synthetic_models[model_cls] = name

        if model_cls in self._resolving_models:
            return name
        self._resolving_models.add(model_cls)
        try:
            self.typing_imports.update({"Any", "Protocol"})
            lines = [f"class {name}(Protocol):"]
            for fname, finfo in model_cls.model_fields.items():
                if fname.isidentifier() and not keyword.iskeyword(fname):
                    ftype = self.render(finfo.annotation) if finfo.annotation is not None else "Any"
                    lines.extend(["    @property", f"    def {fname}(self) -> {ftype}: ..."])
            lines.append("    def model_dump(self, *args: Any, **kwargs: Any) -> dict[str, Any]: ...")
            self._model_defs.append(lines)
        finally:
            self._resolving_models.discard(model_cls)
        return name

    def get_path_protocol(self, fields: tuple[tuple[str, str], ...]) -> str:
        if fields in self._path_protocols:
            return self._path_protocols[fields]
        slug = "_".join(name for name, _ in fields)
        base = f"_PathParams_{slug}" if slug else "_PathParams"
        name = base
        counter = 2
        while name in self.used_names:
            name = f"{base}_{counter}"
            counter += 1
        self.used_names.add(name)
        self._path_protocols[fields] = name

        self.typing_imports.update({"Any", "Protocol"})
        lines = [f"class {name}(Protocol):"]
        for fname, ftype in fields:
            lines.extend(["    @property", f"    def {fname}(self) -> {ftype}: ..."])
        lines.append("    def model_dump(self) -> dict[str, Any]: ...")
        self._path_protocol_defs.append(lines)
        return name

    def render(self, tp: Any) -> str:
        if tp is _EMPTY:
            return "str | int"
        origin = get_origin(tp)
        if origin is Annotated:
            return self.render(get_args(tp)[0])
        if tp is type(None):
            return "None"
        if tp is Any:
            self.typing_imports.add("Any")
            return "Any"

        if origin in (Union, types.UnionType):
            parts: list[str] = []
            for arg in get_args(tp):
                rendered = self.render(arg)
                if rendered not in parts:
                    parts.append(rendered)
            return " | ".join(parts)

        if origin is Literal:
            self.typing_imports.add("Literal")
            lit_parts: list[str] = []
            for arg in get_args(tp):
                if isinstance(arg, Enum):
                    enum_cls = type(arg)
                    mod_name = self._importable_module(enum_cls)
                    if mod_name is not None:
                        cls_ref = enum_cls.__name__ if mod_name == "builtins" else self._import_symbol(mod_name, enum_cls.__name__)
                        lit_parts.append(f"{cls_ref}.{arg.name}")
                    else:
                        lit_parts.append(repr(arg.value))
                else:
                    lit_parts.append(repr(arg))
            return f"Literal[{', '.join(lit_parts)}]"

        if origin in (list, set, frozenset, Sequence, Iterable):
            args = get_args(tp)
            if origin in (Sequence, Iterable):
                self.abc_imports.add(origin.__name__)
                prefix = origin.__name__
            else:
                prefix = origin.__name__
            if args:
                return f"{prefix}[{self.render(args[0])}]"
            self.typing_imports.add("Any")
            return f"{prefix}[Any]"

        if origin is tuple:
            args = get_args(tp)
            if not args:
                self.typing_imports.add("Any")
                return "tuple[Any, ...]"
            if len(args) == 2 and args[1] is Ellipsis:
                return f"tuple[{self.render(args[0])}, ...]"
            return f"tuple[{', '.join(self.render(a) for a in args)}]"

        if origin is dict:
            args = get_args(tp)
            if len(args) == 2:
                return f"dict[{self.render(args[0])}, {self.render(args[1])}]"
            self.typing_imports.add("Any")
            return "dict[str, Any]"

        if inspect.isclass(tp):
            if tp in (str, int, float, bool, bytes, object):
                return tp.__name__
            if tp in (list, set, frozenset):
                self.typing_imports.add("Any")
                return f"{tp.__name__}[Any]"
            if tp is tuple:
                self.typing_imports.add("Any")
                return "tuple[Any, ...]"
            if tp is dict:
                self.typing_imports.add("Any")
                return "dict[str, Any]"

            mod_name = self._importable_module(tp)
            if mod_name is not None:
                if mod_name == "builtins":
                    return tp.__name__
                return self._import_symbol(mod_name, tp.__name__)

            if issubclass(tp, Enum):
                enum_name = self._import_symbol("enum", "Enum")
                vals = [repr(m.value) for m in tp if isinstance(m.value, str | int | bool)]
                if vals:
                    self.typing_imports.add("Literal")
                    return f"{enum_name} | Literal[{', '.join(vals)}]"
                return enum_name
            if issubclass(tp, BaseModel):
                return self._ensure_synthetic_model(tp)
            return "object"

        return "object"

    def render_path_type(self, tp: Any) -> str:
        inner = _unwrap_optional(tp)
        if inner is _EMPTY or inner is Any:
            return "str | int"
        return self.render(inner)

    def render_rest_type(self, tp: Any) -> str:
        inner = _unwrap_optional(tp)
        origin = get_origin(inner)
        if origin is Annotated:
            inner = get_args(inner)[0]
            origin = get_origin(inner)

        elem: Any = _EMPTY
        if origin in (list, set, frozenset, tuple, Sequence, Iterable):
            args = get_args(inner)
            elem = args[0] if args else _EMPTY
        elif inner in (list, set, frozenset, tuple, Sequence, Iterable):
            elem = _EMPTY
        elif inner is not _EMPTY and inner is not Any:
            elem = inner

        elem_str = "str | int" if elem is _EMPTY or elem is Any else self.render(elem)
        self.abc_imports.add("Sequence")
        if elem_str == "str":
            return "Sequence[str] | set[str] | frozenset[str] | None"
        return f"{elem_str} | Sequence[{elem_str}] | set[{elem_str}] | frozenset[{elem_str}] | None"

    def render_query_type(self, tp: Any) -> str:
        if tp is _EMPTY:
            return "str | int | float | bool | list[str | int | float | bool] | tuple[str | int | float | bool, ...] | None"
        inner = _unwrap_optional(tp)
        origin = get_origin(inner)
        if origin is Annotated:
            inner = get_args(inner)[0]
            origin = get_origin(inner)

        if origin in (list, tuple, set, frozenset, Sequence) or inner in (list, tuple, set, frozenset):
            args = get_args(inner)
            elem = args[0] if args else _EMPTY
            elem_str = "str | int | float | bool" if elem is _EMPTY or elem is Any else self.render(elem)
            return f"list[{elem_str}] | tuple[{elem_str}, ...] | set[{elem_str}] | frozenset[{elem_str}] | None"

        rendered = self.render(inner)
        return rendered if rendered == "None" or rendered.endswith(" | None") else f"{rendered} | None"

    def render_model_type(self, model_cls: type[BaseModel]) -> str:
        mod_name = self._importable_module(model_cls)
        if mod_name is not None and mod_name != "builtins":
            return self._import_symbol(mod_name, model_cls.__name__)
        return self._ensure_synthetic_model(model_cls)


def _render_url_for_stub(
    source: RouteTree | Sequence[str],
    project_root: Path,
    *,
    excluded_inputs: AbstractSet[str] = frozenset(),
) -> str:
    if isinstance(source, RouteTree):
        page_ids = sorted(rid for rid in source.nodes if not rid.endswith(")"))
    else:
        page_ids = [rid for rid in source if not rid.endswith(")")]

    renderer = _StubTypeRenderer(project_root)

    if not page_ids:
        renderer.typing_imports.add("Never")
        return "\n".join(
            [
                "from typing import Never",
                "",
                "type RouteId = Never",
                "",
                "def url_for(route_id: Never, *args: object, **kwargs: object) -> str: ...",
                "",
            ]
        )

    renderer.typing_imports.add("Literal")
    signatures: list[str] = []

    for rid in page_ids:
        info = (
            _collect_route_inputs(source, rid, excluded_inputs=excluded_inputs)
            if isinstance(source, RouteTree)
            else _collect_basic_route_inputs(rid)
        )
        rid_lit = f"Literal[{json.dumps(rid)}]"

        if info.invalid_path or info.has_invalid_query:
            signatures.append(
                f"def url_for(route_id: {rid_lit}, params_or_model: object = ..., **kwargs: object) -> str: ..."
            )
            continue

        path_fields = [(name, renderer.render_path_type(tp)) for name, tp in info.path_params]
        rest_type = renderer.render_rest_type(info.rest_type) if info.has_rest else None
        query_fields = [(name, renderer.render_query_type(tp)) for name, tp in info.query_types.items()]

        req_kw = [f"{name}: {ftype}" for name, ftype in path_fields]
        opt_kw = [f"{name}: {ftype} = ..." for name, ftype in path_fields]
        query_kw = ([f"rest: {rest_type} = ..."] if rest_type is not None else []) + [
            f"{name}: {ftype} = ..." for name, ftype in query_fields
        ]

        # 1. Keyword-only overload (no positional model).
        kw_all = [*req_kw, *query_kw]
        if kw_all:
            signatures.append(f"def url_for(route_id: {rid_lit}, *, {', '.join(kw_all)}) -> str: ...")
        else:
            signatures.append(f"def url_for(route_id: {rid_lit}) -> str: ...")

        # 2. Positional path-parameter model overload (when route has `[param]` or `[__rest]`).
        if path_fields or rest_type is not None:
            proto_fields = tuple(path_fields) if path_fields else (("rest", rest_type or "object"),)
            proto_name = renderer.get_path_protocol(proto_fields)
            model_kw = [*opt_kw, *query_kw]
            kw_part = f", *, {', '.join(model_kw)}" if model_kw else ""
            signatures.append(
                f"def url_for(route_id: {rid_lit}, params_or_model: {proto_name}, /{kw_part}) -> str: ..."
            )

        # 3. Positional query model overload(s), keeping path params required as keyword args.
        if info.query_models:
            model_types = " | ".join(renderer.render_model_type(m) for m in info.query_models)
            qmodel_kw = [*req_kw, *query_kw]
            kw_part = f", *, {', '.join(qmodel_kw)}" if qmodel_kw else ""
            signatures.append(
                f"def url_for(route_id: {rid_lit}, params_or_model: {model_types}, /{kw_part}) -> str: ..."
            )

    use_overload = len(signatures) >= 2
    if use_overload:
        renderer.typing_imports.add("overload")

    lines: list[str] = []
    if renderer.abc_imports:
        lines.append(f"from collections.abc import {', '.join(sorted(renderer.abc_imports))}")
    if renderer.typing_imports:
        lines.append(f"from typing import {', '.join(sorted(renderer.typing_imports))}")
    for mod_name in sorted(renderer.imports):
        specs = [
            f"{sym} as {alias}" if sym != alias else sym
            for sym, alias in sorted(renderer.imports[mod_name].items())
        ]
        lines.append(f"from {mod_name} import {', '.join(specs)}")
    lines.append("")

    literals = ", ".join(json.dumps(rid) for rid in page_ids)
    lines.append(f"type RouteId = Literal[{literals}]")
    lines.append("")

    for proto_lines in renderer._path_protocol_defs:
        lines.extend(proto_lines)
        lines.append("")

    for model_lines in renderer._model_defs:
        lines.extend(model_lines)
        lines.append("")

    for sig in signatures:
        if use_overload:
            lines.append("@overload")
        lines.append(sig)
    lines.append("")
    return "\n".join(lines)
