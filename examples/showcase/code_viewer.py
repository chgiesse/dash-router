"""Drawer that shows the source files the router used to render the current URL."""

import sys
from pathlib import Path
from typing import Any

import dash_mantine_components as dmc
from dash import Input, Output, State, callback, clientside_callback, dcc, get_app, html, no_update

from dash_router import DashRouter, MatchedNode, RootContainer

CODE_DRAWER_ID = "code-drawer"
CODE_BUTTON_ID = "code-button"
CODE_CONTENT_ID = "code-content"
CODE_LAST_URL_ID = "code-last-url"
CODE_REQUEST_ID = "code-request"
CODE_TREE_ID = "code-tree"
CODE_VIEW_ID = "code-view"
CODE_FILES_ID = "code-files"
CODE_MARKS_ID = "code-marks"
CODE_MARKS_APPLIED_ID = "code-marks-applied"

APP_DIR = Path(__file__).resolve().parent
PAGES_DIR = APP_DIR / "pages"
NODE_FILES = ("page.py", "api.py", "loading.py", "error.py", "default.py", "models.py")
MODE_COLORS = {"page": "indigo", "default": "yellow", "empty": "gray"}
LANGUAGES = {".py": "python", ".md": "markdown", ".css": "css", ".toml": "toml"}


def code_drawer() -> html.Div:
    return html.Div(
        [
            dmc.Drawer(
                id=CODE_DRAWER_ID,
                position="right",
                size="55%",
                title="Source code of this page",
                children=html.Div(id=CODE_CONTENT_ID),
            ),
            dcc.Store(id=CODE_LAST_URL_ID),
            dcc.Store(id=CODE_REQUEST_ID),
        ]
    )


def _file_entry(path: Path, title: str | None = None) -> dict[str, str]:
    return {"fileName": title or path.name, "code": path.read_text(encoding="utf-8"), "language": "python"}


def source_block(path: Path, title: str | None = None) -> dmc.CodeHighlightTabs:
    return dmc.CodeHighlightTabs(code=[_file_entry(path, title)], withCopyButton=True)


def _node_folder(router: DashRouter, node_id: str) -> Path:
    module = sys.modules.get(router.tree.nodes[node_id].module)
    module_file = getattr(module, "__file__", None)
    if module_file:
        return Path(module_file).parent
    return PAGES_DIR / node_id.strip("/")


def _node_files(router: DashRouter, node: MatchedNode) -> list[Path]:
    folder = _node_folder(router, node.node_id)
    # Only the files the router actually executed: default.py replaces the whole node, and an
    # omitted [param] skips its api.py / loading.py.
    if node.mode == "default":
        used: tuple[str, ...] = ("default.py",)
    elif node.omitted:
        used = ("page.py", "error.py", "models.py")
    else:
        used = tuple(name for name in NODE_FILES if name != "default.py")
    return [folder / name for name in used if (folder / name).is_file()]


def _collect(node: MatchedNode, order: list[MatchedNode]) -> None:
    order.append(node)
    if node.mode == "empty":
        return
    if node.child is not None:
        _collect(node.child, order)
    for slot in node.slots.values():
        _collect(slot, order)


def _rel(path: Path) -> str:
    return path.resolve().relative_to(APP_DIR).as_posix()


def _ancestors(value: str) -> set[str]:
    parts = value.split("/")[:-1]
    return {"/".join(parts[:i]) + "/" for i in range(1, len(parts) + 1)}


def _route_badge(node: MatchedNode) -> dmc.Badge:
    label = node.mode
    return dmc.Badge(f"{node.node_id}: {label}", color=MODE_COLORS.get(node.mode, "gray"), variant="light", size="sm")


def _route_marks(router: DashRouter, rendered: list[MatchedNode]) -> dict[str, str]:
    marks: dict[str, str] = {}
    for node in rendered:
        for path in _node_files(router, node):
            marks.setdefault(_rel(path), node.mode)
    return marks


def _visible(path: Path) -> bool:
    return not path.name.startswith(".") and path.name != "__pycache__"


def _tree_nodes(
    folder: Path, marks: dict[str, str], matched_folders: set[str], files: dict[str, dict[str, str]]
) -> list[dict[str, Any]]:
    # Tree labels must be plain strings in dmc 3; matched files are highlighted with a generated
    # stylesheet keyed on each node's `data-value` (see the clientside callback below).
    entries = sorted((path for path in folder.iterdir() if _visible(path)), key=lambda path: (path.is_file(), path.name))
    nodes: list[dict[str, Any]] = []
    for entry in entries:
        if entry.is_dir():
            value = _rel(entry) + "/"
            nodes.append(
                {"label": entry.name + "/", "value": value, "children": _tree_nodes(entry, marks, matched_folders, files)}
            )
        elif entry.is_file():
            value = _rel(entry)
            files[value] = {"code": entry.read_text(encoding="utf-8"), "language": LANGUAGES.get(entry.suffix, "text")}
            mode = marks.get(value)
            label = f"{entry.name}  ·  {mode}" if mode not in (None, "page") else entry.name
            nodes.append({"label": label, "value": value})
    return nodes


def _selected_value(router: DashRouter, root: MatchedNode | None, files: dict[str, dict[str, str]]) -> str:
    """The page the URL points at: the deepest node of the main `children` chain (not a slot)."""
    if root is None:
        return "app.py"
    leaf = root
    while leaf.child is not None and leaf.child.mode != "empty":
        leaf = leaf.child
    name = "default.py" if leaf.mode == "default" else "page.py"
    value = _rel(_node_folder(router, leaf.node_id) / name)
    return value if value in files else "app.py"


def build_code_view(router: DashRouter, url: str, previous_url: str | None = None) -> dmc.Stack:
    matched = router.match(url)

    order: list[MatchedNode] = []
    if matched is not None:
        _collect(matched.root, order)
    rendered = [node for node in order if node.mode != "empty"]

    marks = _route_marks(router, rendered)
    matched_folders = set().union(*(_ancestors(value) for value in marks))
    files: dict[str, dict[str, str]] = {}
    tree = _tree_nodes(APP_DIR, marks, matched_folders, files)
    selected = _selected_value(router, matched.root if matched is not None else None, files)

    header: list[Any]
    if matched is None:
        header = [dmc.Alert("No route matches this URL.", title="No match", color="red")]
    else:
        header = [
            dmc.Text(f"Route segments matched for {url}", size="sm", c="dimmed"),
            dmc.Group([_route_badge(node) for node in order], gap="xs"),
        ]

    body = dmc.Grid(
        [
            dmc.GridCol(
                dmc.ScrollArea(
                    dmc.Tree(
                        id=CODE_TREE_ID,
                        data=tree,
                        expanded=sorted(matched_folders | {"pages/"}),
                        selected=[selected],
                        selectOnClick=True,
                        # dmc 3 Tree reads `checked` on every data change; an explicit list avoids a crash.
                        checked=[],
                    ),
                    h="calc(100vh - 180px)",
                ),
                span=4,
            ),
            dmc.GridCol(
                dmc.CodeHighlightTabs(
                    id=CODE_VIEW_ID,
                    code=[{"fileName": selected, **files[selected]}],
                    withCopyButton=True,
                ),
                span=8,
            ),
        ],
        gap="md",
    )
    marks_data = {"files": sorted(marks), "folders": sorted(matched_folders)}
    return dmc.Stack(
        [
            *header,
            body,
            dcc.Store(id=CODE_FILES_ID, data=files),
            dcc.Store(id=CODE_MARKS_ID, data=marks_data),
            dcc.Store(id=CODE_MARKS_APPLIED_ID),
        ],
        gap="md",
    )


# Track the URL client-side and only ask the server for sources while the drawer is open, so
# browsing with the drawer closed sends no extra requests.
clientside_callback(
    """
    function(pathname, search, opened, last) {
        const dc = window.dash_clientside;
        const url = (pathname || "/") + (search || "");
        last = last || {};
        const previous = last.url === url ? last.previous : last.url;
        const state = { url: url, previous: previous || null };
        return [state, opened ? Object.assign({ t: Date.now() }, state) : dc.no_update];
    }
    """,
    Output(CODE_LAST_URL_ID, "data"),
    Output(CODE_REQUEST_ID, "data"),
    Input(RootContainer.ids.location, "pathname"),
    Input(RootContainer.ids.location, "search"),
    Input(CODE_DRAWER_ID, "opened"),
    State(CODE_LAST_URL_ID, "data"),
)


@callback(
    Output(CODE_CONTENT_ID, "children"),
    Input(CODE_REQUEST_ID, "data"),
    prevent_initial_call=True,
)
def render_code_view(request: dict | None) -> Any:
    if not request:
        return no_update
    return build_code_view(get_app().router, request["url"], request.get("previous"))


clientside_callback(
    """
    function(selected, files) {
        const path = (selected || [])[0];
        if (!files || !Object.prototype.hasOwnProperty.call(files, path)) {
            return window.dash_clientside.no_update;
        }
        return [{ fileName: path, code: files[path].code, language: files[path].language }];
    }
    """,
    Output(CODE_VIEW_ID, "code"),
    Input(CODE_TREE_ID, "selected"),
    State(CODE_FILES_ID, "data"),
    prevent_initial_call=True,
)


clientside_callback(
    """
    function(n_clicks, opened) {
        return n_clicks ? !opened : window.dash_clientside.no_update;
    }
    """,
    Output(CODE_DRAWER_ID, "opened"),
    Input(CODE_BUTTON_ID, "n_clicks"),
    State(CODE_DRAWER_ID, "opened"),
    prevent_initial_call=True,
)


# Highlight the files the router used for this URL. The Tree re-renders its nodes on every
# expand/collapse, so the styling lives in a <style> element rather than on the nodes.
clientside_callback(
    """
    function(marks) {
        if (!marks) return window.dash_clientside.no_update;
        let el = document.getElementById("code-tree-marks");
        if (!el) {
            el = document.createElement("style");
            el.id = "code-tree-marks";
            document.head.appendChild(el);
        }
        // Tree values are project-relative paths (no quotes or backslashes).
        const sel = v => '#code-tree li[data-value="' + v + '"] > .mantine-Tree-label';
        const files = marks.files.map(sel);
        const folders = marks.folders.map(sel);
        el.textContent =
            "#code-tree .mantine-Tree-label { color: var(--mantine-color-dimmed); }\\n" +
            "#code-tree .mantine-Tree-label[data-selected] { background: var(--mantine-color-indigo-light); }\\n" +
            (folders.length ? folders.join(",") + " { color: var(--mantine-color-text); font-weight: 600; }\\n" : "") +
            (files.length ? files.join(",") + " { color: var(--mantine-color-indigo-4); font-weight: 700; }\\n" : "");
        return Date.now();
    }
    """,
    Output(CODE_MARKS_APPLIED_ID, "data"),
    Input(CODE_MARKS_ID, "data"),
)
