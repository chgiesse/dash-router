from pathlib import Path
from textwrap import dedent
from typing import Any

import pytest

from dash_router import RouteTree
from dash_router.errors import RouteConfigConflictError, RouteLayoutMissingError

ROLE_ATTRS = {"page": "layout", "loading": "loading_layout", "error": "error_layout", "default": "default_layout"}


def _write(path: Path, code: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(code).lstrip(), encoding="utf-8")


def _where(fn: Any) -> str:
    return f"{Path(fn.__code__.co_filename).name}:{fn.__name__}"


def test_role_names_in_all_route_files(tmp_path: Path):
    pages = tmp_path / "pages"
    body = """
        from dash import html

        def {name}(**_):
            return html.Div("{name}")
        """
    _write(pages / "page.py", body.format(name="page"))
    _write(pages / "sub" / "page.py", body.format(name="page"))
    _write(pages / "sub" / "loading.py", body.format(name="loading"))
    _write(pages / "sub" / "error.py", body.format(name="error").replace("**_", "error: Exception, **_"))
    _write(pages / "sub" / "default.py", body.format(name="default"))

    tree = RouteTree.from_folder(pages)

    root = tree.nodes["/"]
    assert _where(root.layout) == "page.py:page"
    sub = tree.nodes["sub"]
    assert _where(sub.layout) == "page.py:page"
    assert _where(sub.loading_layout) == "loading.py:loading"
    assert _where(sub.error_layout) == "error.py:error"
    assert _where(sub.default_layout) == "default.py:default"


@pytest.mark.parametrize("stem", ["page", "loading", "error", "default"])
def test_layout_is_accepted_as_fallback(tmp_path: Path, stem: str):
    pages = tmp_path / "pages"
    if stem == "page":
        _write(pages / "page.py", "def layout(**_):\n    return None\n")
    else:
        _write(pages / "page.py", "def page(**_):\n    return None\n")
        _write(pages / f"{stem}.py", "def layout(**_):\n    return None\n")

    tree = RouteTree.from_folder(pages)

    assert _where(getattr(tree.nodes["/"], ROLE_ATTRS[stem])) == f"{stem}.py:layout"


@pytest.mark.parametrize("stem", ["page", "loading", "error", "default"])
def test_defining_role_name_and_layout_is_an_error(tmp_path: Path, stem: str):
    pages = tmp_path / "pages"
    both = "def {stem}(**_):\n    return None\n\ndef layout(**_):\n    return None\n"
    if stem == "page":
        _write(pages / "page.py", both.format(stem=stem))
    else:
        _write(pages / "page.py", "def page(**_):\n    return None\n")
        _write(pages / f"{stem}.py", both.format(stem=stem))

    with pytest.raises(RouteConfigConflictError, match="defines both"):
        RouteTree.from_folder(pages)


def test_page_without_page_or_layout_is_an_error(tmp_path: Path):
    pages = tmp_path / "pages"
    _write(pages / "page.py", "def other(**_):\n    return None\n")

    with pytest.raises(RouteLayoutMissingError, match="must define `page`"):
        RouteTree.from_folder(pages)


@pytest.mark.parametrize("stem", ["default", "loading", "error"])
def test_route_file_without_its_name_or_layout_is_an_error(tmp_path: Path, stem: str):
    pages = tmp_path / "pages"
    _write(pages / "page.py", "def page(**_):\n    return None\n")
    _write(pages / f"{stem}.py", "def other(**_):\n    return None\n")

    with pytest.raises(RouteLayoutMissingError, match=f"must define `{stem}`"):
        RouteTree.from_folder(pages)
