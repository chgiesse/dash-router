import json
import os
import shutil
import subprocess
import sys
import time
from enum import Enum
from pathlib import Path
from textwrap import dedent

import pytest
from dash import Dash, State
from pydantic import BaseModel, Field

from dash_router import DashRouter, url_for
from dash_router._url_for import _ROUTE_QUERY_KEYS


def _write(path: Path, code: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(code).lstrip(), encoding="utf-8")


@pytest.fixture(autouse=True)
def _clear_route_query_registry():
    snapshot = dict(_ROUTE_QUERY_KEYS)
    yield
    _ROUTE_QUERY_KEYS.clear()
    _ROUTE_QUERY_KEYS.update(snapshot)


class Status(str, Enum):
    ALL = "all"
    OPEN = "open"
    CLOSED = "closed"


class Filters(BaseModel):
    status: Status = Status.ALL
    q: str = ""
    page: int = Field(default=1, ge=1)
    tags: list[str] = Field(default_factory=list)


class OrderRef(BaseModel):
    order_id: int


class OrderDomainModel(BaseModel):
    order_id: int
    customer_id: int
    total: float


def test_url_for_runtime_path_and_query_serialization():
    assert url_for("/") == "/"
    assert url_for("/", status=Status.OPEN, active=True, tags=["eu", "us"], empty=[], omitted=None) == (
        "/?status=open&active=true&tags=eu,us"
    )
    assert url_for("orders/[order_id]", OrderRef(order_id=1003)) == "/orders/1003"
    assert url_for("orders/[order_id]", OrderDomainModel(order_id=1003, customer_id=5, total=42.5)) == "/orders/1003"
    assert url_for("orders", Filters()) == "/orders"
    assert url_for("orders", Filters(status=Status.OPEN, page=2, tags=["a", "b"])) == (
        "/orders?status=open&page=2&tags=a,b"
    )
    assert url_for("orders/[order_id]", Filters(status=Status.CLOSED, page=3), order_id=1003, page=None) == (
        "/orders/1003?status=closed"
    )
    assert url_for("orders/[order_id]", order_id=Status.OPEN) == "/orders/open"
    assert url_for("docs/[__rest]", rest=["guides", "routing"]) == "/docs/guides/routing"
    assert url_for("docs/[__rest]", rest="intro") == "/docs/intro"
    assert url_for("docs/[__rest]") == "/docs"


def test_dash_router_registers_query_keys_to_filter_domain_models():
    DashRouter.from_spec(
        {
            "orders": {
                "[order_id]": {
                    "layout": lambda order_id, status="all", **_: None,
                }
            }
        }
    )

    class OrderWithStatus(BaseModel):
        order_id: int
        status: Status = Status.ALL
        internal_total: float = 99.0

    # `internal_total` is not a declared query param of `orders/[order_id]`, so it is not serialized.
    assert url_for("orders/[order_id]", OrderWithStatus(order_id=42, status=Status.OPEN)) == "/orders/42?status=open"


def test_auto_stub_generation_reload_and_idempotency(tmp_path: Path):
    pages = tmp_path / "pages"
    _write(
        tmp_path / "models.py",
        """
        from enum import Enum
        from pydantic import BaseModel, Field

        class OrderStatus(str, Enum):
            ALL = "all"
            OPEN = "open"

        class OrderFilters(BaseModel):
            status: OrderStatus = OrderStatus.ALL
            page: int = Field(default=1, ge=1)
        """,
    )
    _write(
        pages / "page.py",
        """
        from dash import html

        def page(children=None, theme: str = "light", **_):
            return html.Div(children)
        """,
    )
    _write(
        pages / "orders" / "page.py",
        """
        from dash import html
        from dash_router import RouteConfig

        config = RouteConfig(default_child="all")

        def page(children=None, **_):
            return html.Div(children)
        """,
    )
    _write(
        pages / "orders" / "all" / "page.py",
        """
        from dash import html

        def page(**_):
            return html.Div("all")
        """,
    )
    _write(
        pages / "orders" / "(listing)" / "page.py",
        """
        from dash import html
        from models import OrderFilters

        def page(filters: OrderFilters, **_):
            return html.Div(str(filters.page))
        """,
    )
    _write(
        pages / "orders" / "[order_id]" / "page.py",
        """
        from dash import html

        def page(order_id: int | None = None, **_):
            return html.Div(str(order_id))
        """,
    )
    _write(
        pages / "docs" / "[__rest]" / "page.py",
        """
        from dash import html

        def page(rest: list[str], **_):
            return html.Div("/".join(rest))
        """,
    )

    sys.path.insert(0, str(tmp_path))
    try:
        app = Dash(__name__, use_pages=False)
        app.routing_callback_inputs = {"theme": State("theme-switch", "value")}  # type: ignore[attr-defined]
        router = DashRouter(app, pages_folder=pages)

        stub_dir = tmp_path / "typings" / "dash_router-stubs"
        stub_file = stub_dir / "_url_for.pyi"
        assert (stub_dir / "py.typed").read_text(encoding="utf-8") == "partial\n"
        assert (stub_dir / ".gitignore").read_text(encoding="utf-8") == "*\n"
        assert stub_file.is_file()

        content = stub_file.read_text(encoding="utf-8")
        # `theme` from routing_callback_inputs must be excluded.
        assert "theme:" not in content
        # `order_id` strips `| None` and is typed as `int`.
        assert "order_id: int" in content
        # `orders/(listing)` propagates `OrderFilters` onto `orders` and `orders/[order_id]`.
        assert "OrderFilters" in content
        assert "status: OrderStatus | None = ..." in content
        assert "page: int | None = ..." in content
        # `docs/[__rest]` extracts `str` element type.
        assert "rest: Sequence[str]" in content

        # Reloading without changes must NOT rewrite the stub (preserving mtime).
        before_ns = stub_file.stat().st_mtime_ns
        time.sleep(0.02)
        router.reload()
        assert stub_file.stat().st_mtime_ns == before_ns

        # Adding a new route and calling reload() updates the stub automatically.
        _write(
            pages / "reports" / "[report_id]" / "page.py",
            """
            from dash import html

            def page(report_id: str, include_archived: bool = False, **_):
                return html.Div(report_id)
            """,
        )
        router.reload()
        updated = stub_file.read_text(encoding="utf-8")
        assert '"reports/[report_id]"' in updated
        assert "report_id: str" in updated
        assert "include_archived: bool | None = ..." in updated
    finally:
        if str(tmp_path) in sys.path:
            sys.path.remove(str(tmp_path))
        for mod_name in [m for m in sys.modules if m == "models" or m == "pages" or m.startswith("pages.")]:
            sys.modules.pop(mod_name, None)


def test_from_spec_does_not_generate_stubs_by_default(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(tmp_path)
    DashRouter.from_spec({"home": {}})
    assert not (tmp_path / "typings").exists()


def test_unimportable_slot_model_falls_back_to_structural_protocol(tmp_path: Path):
    pages = tmp_path / "pages"
    _write(
        pages / "orders" / "(listing)" / "models.py",
        """
        from enum import Enum
        from pydantic import BaseModel

        class Scope(str, Enum):
            MINE = "mine"
            TEAM = "team"

        class SlotFilters(BaseModel):
            scope: Scope = Scope.MINE
            limit: int = 20
        """,
    )
    _write(
        pages / "orders" / "page.py",
        """
        from dash import html

        def page(listing=None, **_):
            return html.Div(listing)
        """,
    )
    _write(
        pages / "orders" / "(listing)" / "page.py",
        """
        from dash import html
        from .models import SlotFilters

        def page(filters: SlotFilters, **_):
            return html.Div(str(filters.limit))
        """,
    )

    DashRouter(pages_folder=pages)
    stub = (tmp_path / "typings" / "dash_router-stubs" / "_url_for.pyi").read_text(encoding="utf-8")
    # `(listing)` is not a valid Python package name, so we must not emit `from pages.orders.listing.models ...`.
    assert "listing.models" not in stub
    assert "class _QueryModel_SlotFilters(Protocol):" in stub
    assert "Enum | Literal['mine', 'team']" in stub
    assert "limit: int | None = ..." in stub


def test_basedpyright_validates_generated_stubs(tmp_path: Path):
    basedpyright = shutil.which("basedpyright") or str(Path(sys.executable).parent / "basedpyright")
    if not Path(basedpyright).exists() and shutil.which("basedpyright") is None:
        pytest.skip("basedpyright executable not found")

    pages = tmp_path / "pages"
    _write(
        tmp_path / "models.py",
        """
        from enum import Enum
        from pydantic import BaseModel

        class OrderStatus(str, Enum):
            ALL = "all"
            OPEN = "open"

        class OrderFilters(BaseModel):
            status: OrderStatus = OrderStatus.ALL
            page: int = 1
        """,
    )
    _write(
        pages / "page.py",
        """
        from dash import html

        def page(children=None, **_):
            return html.Div(children)
        """,
    )
    _write(
        pages / "orders" / "page.py",
        """
        from dash import html

        def page(children=None, listing=None, **_):
            return html.Div([listing, children])
        """,
    )
    _write(
        pages / "orders" / "(listing)" / "page.py",
        """
        from dash import html
        from models import OrderFilters

        def page(filters: OrderFilters, **_):
            return html.Div(str(filters.page))
        """,
    )
    _write(
        pages / "orders" / "[order_id]" / "page.py",
        """
        from dash import html

        def page(order_id: int, **_):
            return html.Div(str(order_id))
        """,
    )
    _write(
        pages / "docs" / "[__rest]" / "page.py",
        """
        from dash import html

        def page(rest: list[str], **_):
            return html.Div("/".join(rest))
        """,
    )

    sys.path.insert(0, str(tmp_path))
    try:
        DashRouter(pages_folder=pages)
    finally:
        if str(tmp_path) in sys.path:
            sys.path.remove(str(tmp_path))
        for mod_name in [m for m in sys.modules if m == "models" or m == "pages" or m.startswith("pages.")]:
            sys.modules.pop(mod_name, None)

    dash_router_src = Path(__file__).resolve().parents[1] / "src"
    venv_dir = Path(sys.prefix)
    (tmp_path / "pyrightconfig.json").write_text(
        json.dumps(
            {
                "extraPaths": [str(tmp_path), str(dash_router_src)],
                "venvPath": str(venv_dir.parent),
                "venv": venv_dir.name,
                "typeCheckingMode": "basic",
            }
        ),
        encoding="utf-8",
    )

    _write(
        tmp_path / "check_valid.py",
        """
        from pydantic import BaseModel
        from dash_router import DashRouter, Link, RouteConfig, RouteId, url_for
        from models import OrderFilters, OrderStatus

        class OrderRef(BaseModel):
            order_id: int

        _keep = (DashRouter, Link, RouteConfig)
        rid: RouteId = "orders/[order_id]"
        filters = OrderFilters(status=OrderStatus.OPEN, page=2)

        u1: str = url_for("/")
        u2: str = url_for("orders")
        u3: str = url_for("orders", status=OrderStatus.OPEN, page=2)
        u4: str = url_for("orders", filters)
        u5: str = url_for("orders", filters, page=3)
        u6: str = url_for("orders/[order_id]", order_id=1003)
        u7: str = url_for("orders/[order_id]", OrderRef(order_id=1003))
        u8: str = url_for("orders/[order_id]", filters, order_id=1003)
        u9: str = url_for("docs/[__rest]")
        u10: str = url_for("docs/[__rest]", rest=["guides", "routing"])
        u11: str = url_for("docs/[__rest]", rest="intro")
        """,
    )
    _write(
        tmp_path / "check_invalid.py",
        """
        from pydantic import BaseModel
        from dash_router import RouteId, url_for
        from models import OrderFilters

        class WrongRef(BaseModel):
            customer_id: int

        bad_rid: RouteId = "nonexistent"
        e1 = url_for("nonexistent")
        e2 = url_for("orders/[order_id]")
        e3 = url_for("orders/[order_id]", order_id="not-an-int")
        e4 = url_for("orders/[order_id]", WrongRef(customer_id=1))
        e5 = url_for("orders/[order_id]", OrderFilters())
        e6 = url_for("orders", status="invalid")
        e7 = url_for("orders", bogus=1)
        """,
    )

    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    ok_res = subprocess.run(
        [basedpyright, "-p", str(tmp_path / "pyrightconfig.json"), str(tmp_path / "check_valid.py")],
        capture_output=True,
        text=True,
        env=env,
    )
    assert ok_res.returncode == 0, ok_res.stdout + ok_res.stderr

    bad_res = subprocess.run(
        [basedpyright, "-p", str(tmp_path / "pyrightconfig.json"), str(tmp_path / "check_invalid.py")],
        capture_output=True,
        text=True,
        env=env,
    )
    assert bad_res.returncode != 0
    assert "nonexistent" in bad_res.stdout
    assert "check_invalid.py:9:" in bad_res.stdout
    assert "check_invalid.py:10:" in bad_res.stdout
    assert "check_invalid.py:11:" in bad_res.stdout
    assert "check_invalid.py:12:" in bad_res.stdout
    assert "check_invalid.py:13:" in bad_res.stdout
    assert "check_invalid.py:14:" in bad_res.stdout
    assert "check_invalid.py:15:" in bad_res.stdout


def test_url_for_and_match_roundtrip_special_path_chars():
    from dash_router import DashRouter, Url, url_for

    router = DashRouter.from_spec({"tickets": {"[id]": {}}, "docs": {"[__rest]": {}}})

    built = url_for("tickets/[id]", id="a/b?c=1#x")
    assert built == "/tickets/a%2Fb%3Fc%3D1%23x"
    matched = router.match(built)
    assert matched is not None
    assert matched.root.find_node("tickets/[id]") is not None
    assert matched.root.find_node("tickets/[id]").path_vars["id"] == "a/b?c=1#x"  # type: ignore[union-attr]

    spaced = router.match("/tickets/a%20b")
    assert spaced is not None
    assert spaced.root.find_node("tickets/[id]").path_vars["id"] == "a b"  # type: ignore[union-attr]

    rest_url = url_for("docs/[__rest]", rest=["a b", "c/d?e=1"])
    assert rest_url == "/docs/a%20b/c%2Fd%3Fe%3D1"
    rest_matched = router.match(rest_url)
    assert rest_matched is not None
    assert rest_matched.root.find_node("docs/[__rest]").path_vars["rest"] == ["a b", "c/d?e=1"]  # type: ignore[union-attr]

    # Url.parse(url_for(...)).to_href() preserves percent-encoded segments without double-encoding,
    # while Url(pathname=...) still escapes raw query/fragment delimiters or spaces.
    assert Url.parse(built).set_param("tab", "1").to_href() == "/tickets/a%2Fb%3Fc%3D1%23x?tab=1"
    assert Url(pathname="/tickets/a b?c=1#x").to_href() == "/tickets/a%20b%3Fc=1%23x"
