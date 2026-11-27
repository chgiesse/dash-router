"""Build a `RouteTree` from a `pages/` folder."""

import os
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from importlib.machinery import ModuleSpec
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType
from typing import Any

from ..errors import (
    RouteConfigConflictError,
    RouteLayoutMissingError,
    RouteModuleImportError,
)
from ..types import ErrorLayout, NodeKind
from .tree import RouteConfig, RouteNode, RouteTree, classify_segment, node_id_for, passthrough_layout

_ROUTE_FILES = ("page.py", "default.py")


def load_folder(
    pages_folder: str | Path,
    ignore_empty_folders: bool = False,
    default_error_layout: ErrorLayout | None = None,
    package_prefix: str = "pages",
) -> RouteTree:
    root = Path(pages_folder).resolve()
    if not root.exists():
        raise FileNotFoundError(f"Pages folder not found at: {root}")
    loader = _FolderLoader(root, package_prefix, default_error_layout, ignore_empty_folders)
    with _on_sys_path(root.parent):
        loader.scan(root, rel_parts=(), pending=(), parent=None)
    loader.tree.finalize()
    return loader.tree


class _FolderLoader:
    def __init__(
        self,
        root: Path,
        package_prefix: str,
        default_error_layout: ErrorLayout | None,
        ignore_empty_folders: bool,
    ) -> None:
        self.tree = RouteTree(default_error_layout)
        self.root = root
        self.package_prefix = package_prefix
        self.ignore_empty_folders = ignore_empty_folders
        self._modules: dict[Path, ModuleType] = {}

    def scan(
        self,
        directory: Path,
        rel_parts: tuple[str, ...],
        pending: tuple[str, ...],
        parent: RouteNode | None,
    ) -> None:
        """`pending` collects the URL segments of folders without `page.py` above this one."""
        entries = sorted(os.listdir(directory))
        kind, name = classify_segment(rel_parts[-1] if rel_parts else "/", is_root=not rel_parts)
        has_page = "page.py" in entries
        # A `(slot)` folder without `page.py` still counts when it has `default.py` or routes below.
        is_passthrough_slot = (
            not has_page and kind == "slot" and ("default.py" in entries or _has_route_files(directory))
        )

        if has_page or is_passthrough_slot:
            node = self._load_node(directory, rel_parts, kind, name, pending, has_page)
            self.tree.add_node(node, parent)
            parent, pending = (None if node.kind == "root" else node), ()
        elif rel_parts and kind == "route" and not self.ignore_empty_folders:
            pending = (*pending, name)

        for entry in entries:
            sub = directory / entry
            if not entry.startswith((".", "_")) and sub.is_dir():
                self.scan(sub, (*rel_parts, entry), pending, parent)

    def _load_node(
        self,
        directory: Path,
        rel_parts: tuple[str, ...],
        kind: NodeKind,
        name: str,
        pending: tuple[str, ...],
        has_page: bool,
    ) -> RouteNode:
        node_id = node_id_for(rel_parts)
        package = _ensure_package_chain(self.root, rel_parts, self.package_prefix)
        page_file = directory / "page.py"
        page = self._import(page_file, f"{package}.page") if has_page else None
        layout = _required_layout(page, page_file) if page is not None else passthrough_layout
        raw_config = getattr(page, "config", None) if page is not None else None
        config = raw_config if isinstance(raw_config, RouteConfig) else RouteConfig()

        api = self._import_if_exists(directory / "api.py", f"{package}.api")
        for stem in ("callback", "callbacks"):
            self._import_if_exists(directory / f"{stem}.py", f"{package}.{stem}")

        if kind == "route":
            route_segments = (*pending, name)
        elif kind in ("param", "catch_all"):
            route_segments = pending
        else:
            route_segments = ()
        return RouteNode(
            node_id=node_id,
            kind=kind,
            name=name,
            route_segments=route_segments,
            module=f"{package}.page",
            config=config,
            layout=layout,
            default_layout=self._layout_file(directory, package, "default", config.default_layout),
            loading_layout=self._layout_file(directory, package, "loading", config.loading),
            error_layout=self._layout_file(directory, package, "error", config.error),
            endpoint=getattr(api, "endpoint", None),
            is_passthrough=not has_page,
        )

    def _layout_file(self, directory: Path, package: str, stem: str, configured: Any) -> Any:
        """`<stem>` (or `layout`) from `<stem>.py`, or the one configured in `RouteConfig` (not both)."""
        file = directory / f"{stem}.py"
        if not file.exists():
            return configured
        if configured is not None:
            raise RouteConfigConflictError(
                f"Route config conflict for '{node_id_for(file.parent.relative_to(self.root).parts)}': "
                f"{stem} layout defined in both RouteConfig and {stem}.py."
            )
        module = self._import(file, f"{package}.{stem}")
        # An existing file that defines nothing is a mistake (e.g. a typo in the function name), not "no layout".
        return _required_layout(module, file)

    def _import_if_exists(self, file: Path, module_name: str) -> ModuleType | None:
        return self._import(file, module_name) if file.exists() else None

    def _import(self, file: Path, module_name: str) -> ModuleType:
        if file in self._modules:
            return self._modules[file]
        try:
            spec = spec_from_file_location(module_name, str(file))
            if spec is None or spec.loader is None:
                raise ImportError(f"Cannot create module spec for {file}")
            module = module_from_spec(spec)
            module.__package__ = module_name.rpartition(".")[0]
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
        except Exception as exc:
            sys.modules.pop(module_name, None)
            raise RouteModuleImportError(
                f"Failed to import route module '{module_name}' from {file}: {exc.__class__.__name__}: {exc}"
            ) from exc
        self._modules[file] = module
        return module


def _route_attr(module: ModuleType, file: Path) -> Any:
    """The component or function a route file defines: named after the file (`page`, `loading`,
    `error`, `default`), with `layout` accepted in every file for compatibility. Defining both is ambiguous."""
    role = file.stem
    named = getattr(module, role, None)
    fallback = getattr(module, "layout", None)
    if named is not None and fallback is not None and named is not fallback:
        raise RouteConfigConflictError(
            f"Route file {file} defines both `{role}` and `layout`; keep one (`{role}` is preferred)."
        )
    return named if named is not None else fallback


def _required_layout(module: ModuleType, file: Path) -> Any:
    layout = _route_attr(module, file)
    if layout is None:
        raise RouteLayoutMissingError(f"Route file {file} must define `{file.stem}` (or `layout`).")
    return layout


def _has_route_files(directory: Path) -> bool:
    for entry in os.listdir(directory):
        sub = directory / entry
        if entry.startswith((".", "_")):
            continue
        if (entry in _ROUTE_FILES and sub.is_file()) or (sub.is_dir() and _has_route_files(sub)):
            return True
    return False


@contextmanager
def _on_sys_path(path: Path) -> Iterator[None]:
    """Make the folder containing `pages/` importable while route modules load."""
    entry = str(path)
    added = entry not in sys.path
    if added:
        sys.path.insert(0, entry)
    try:
        yield
    finally:
        if added and entry in sys.path:
            sys.path.remove(entry)


def _ensure_package_chain(root: Path, rel_parts: tuple[str, ...], prefix: str) -> str:
    """Register a synthetic package for every route folder, so route modules can use relative
    imports even though `(slot)` / `[param]` folder names are not Python identifiers.
    Returns the package name of the innermost folder.
    """
    _register_package(prefix, root, replace=False)
    package, path = prefix, root
    for raw in rel_parts:
        path = path / raw
        clean = raw.strip("()[]").replace("-", "_").replace(" ", "_") or "index"
        if clean[0].isdigit():
            clean = f"r_{clean}"
        parent, package = package, f"{package}.{clean}"
        created = _register_package(package, path)
        if created is not None:
            setattr(sys.modules[parent], clean, created)
    return package


def _register_package(name: str, path: Path, replace: bool = True) -> ModuleType | None:
    existing = sys.modules.get(name)
    if existing is not None and (not replace or getattr(existing, "__path__", None) == [str(path)]):
        return None
    package = ModuleType(name)
    package.__path__ = [str(path)]
    package.__package__ = name
    package.__spec__ = ModuleSpec(name, loader=None, is_package=True)
    package.__spec__.submodule_search_locations = [str(path)]
    sys.modules[name] = package
    return package
