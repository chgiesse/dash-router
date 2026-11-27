"""`(old_url, new_url) -> rendered segments` tests for the showcase, one per tour step.

Run: `pytest packages/dash-router/examples/showcase/tests`
"""

import sys
from pathlib import Path

import pytest

SHOWCASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SHOWCASE))

from dash_router import ChildContainer, RootContainer, RouteTester, SlotContainer  # noqa: E402
from docs_site import DOC_PAGES, load_doc  # noqa: E402

OVERVIEW_SLOTS = ["overview/(activity)", "overview/(kpis)", "overview/(live)", "overview/(revenue)"]


@pytest.fixture(scope="module")
def tester() -> RouteTester:
    import app

    return RouteTester(app.router)


def test_root_shell_mounts_once_and_default_child_resolves(tester: RouteTester) -> None:
    tester.assert_routes(old=None, new="/", expected=["/", "overview", *OVERVIEW_SLOTS])
    res = tester.assert_routes(
        old="/overview", new="/orders", expected=["orders", "orders/[order_id]", "orders/(listing)"]
    )
    assert res.targets == [ChildContainer.ids.container("/")]


def test_query_param_only_rerenders_the_subscribing_slot(tester: RouteTester) -> None:
    res = tester.assert_routes(old="/overview", new="/overview?range=7d", expected=["overview/(revenue)"])
    assert res.targets == [SlotContainer.ids.container("overview", "revenue")]
    tester.assert_routes(old="/overview", new="/overview?fail=activity", expected=["overview/(activity)"])


def test_orders_omits_param_to_default_and_detail_resolves_default_child(tester: RouteTester) -> None:
    tester.assert_routes(
        old=None,
        new="/orders",
        expected=["/", "orders", "orders/[order_id]", "orders/(listing)"],
        expected_modes={"orders/[order_id]": "default"},
        expected_vars={"orders/[order_id]": {"order_id": None}},
    )
    tester.assert_routes(
        old="/orders",
        new="/orders/1003",
        expected=["orders/[order_id]", "orders/[order_id]/summary"],
        expected_modes={"orders/[order_id]": "page"},
        expected_vars={"orders/[order_id]": {"order_id": "1003"}},
    )
    tester.assert_routes(old="/orders", new="/orders/1003/summary", expected=["orders/[order_id]", "orders/[order_id]/summary"])


def test_selecting_orders_keeps_the_filtered_list(tester: RouteTester) -> None:
    res = tester.assert_routes(
        old="/orders?status=delayed",
        new="/orders/1003?status=delayed",
        expected=["orders/[order_id]", "orders/[order_id]/summary"],
    )
    assert res.targets == [ChildContainer.ids.container("orders")]
    tester.assert_routes(old="/orders/1003", new="/orders/1003?status=open", expected=["orders/(listing)"])
    # `page=1` is the model default: nothing to render.
    tester.assert_routes(old="/orders", new="/orders?page=1", expected=[])


def test_order_tabs_only_patch_the_tab_container(tester: RouteTester) -> None:
    res = tester.assert_routes(old="/orders/1003", new="/orders/1003/timeline", expected=["orders/[order_id]/timeline"])
    assert res.targets == [ChildContainer.ids.container("orders/[order_id]")]


def test_parallel_routes_default_and_empty_slots(tester: RouteTester) -> None:
    tester.assert_routes(
        old=None,
        new="/customers/accounts/3",
        expected=[
            "/",
            "customers",
            "customers/accounts/[customer_id]",
            "customers/(inspector)",
            "customers/(inspector)/accounts/[customer_id]",
            "customers/(pinned)",
            "customers/(pinned)/accounts/[customer_id]",
        ],
        expected_vars={
            "customers/accounts/[customer_id]": {"customer_id": "3"},
            "customers/(inspector)/accounts/[customer_id]": {"customer_id": "3"},
        },
    )
    tester.assert_routes(
        old="/customers/accounts/3",
        new="/customers/segments",
        expected=["customers/segments", "customers/(inspector)", "customers/(pinned)/segments"],
        expected_modes={"customers/(inspector)": "default"},
    )
    # Nothing is retained: `(pinned)` has no `default.py`, so it renders empty while `(inspector)` shows its default.
    tester.assert_routes(
        old="/customers/accounts/3",
        new="/customers/insights",
        expected=["customers/insights", "customers/(inspector)"],
        expected_modes={"customers/(inspector)": "default", "customers/(pinned)": "empty"},
    )
    # A hard load is matched the same way.
    tester.assert_routes(
        old=None,
        new="/customers/insights",
        expected=["/", "customers", "customers/insights", "customers/(inspector)"],
        expected_modes={"customers/(inspector)": "default", "customers/(pinned)": "empty"},
    )


def test_edge_cases_tabs_and_history_patch_only_their_children(tester: RouteTester) -> None:
    tester.assert_routes(
        old=None,
        new="/edge-cases/tabs-segment",
        expected=["/", "edge-cases", "edge-cases/tabs-segment", "edge-cases/tabs-segment/a"],
    )
    res = tester.assert_routes(
        old="/edge-cases/tabs-segment",
        new="/edge-cases/tabs-segment/b",
        expected=["edge-cases/tabs-segment/b"],
    )
    assert res.targets == [ChildContainer.ids.container("edge-cases/tabs-segment")]
    tester.assert_routes(
        old="/edge-cases/history-superseded",
        new="/edge-cases/history-superseded/fast",
        expected=["edge-cases/history-superseded/fast"],
    )


def test_catch_all_docs(tester: RouteTester) -> None:
    tester.assert_routes(
        old=None,
        new="/docs",
        expected=["/", "docs", "docs/[__rest]"],
        expected_modes={"docs/[__rest]": "default"},
    )
    tester.assert_routes(
        old="/docs",
        new="/docs/fulfilment/shipping/returns",
        expected=["docs/[__rest]"],
        expected_vars={"docs/[__rest]": {"rest": ["fulfilment", "shipping", "returns"]}},
    )


def test_static_wall_display_bypasses_the_shell(tester: RouteTester) -> None:
    res = tester.assert_routes(old="/overview", new="/status", expected=["status"])
    assert res.targets == [RootContainer.ids.container]
    tester.assert_routes(old="/status", new="/overview", expected=["/", "overview", *OVERVIEW_SLOTS])


def test_settings_saved_target_and_404(tester: RouteTester) -> None:
    tester.assert_routes(old="/settings/profile", new="/settings/saved?name=Ada", expected=["settings/saved"])
    assert not tester.transition(old="/overview", new="/does/not/exist").matched


def test_documentation_omitted_topic_renders_overview(tester: RouteTester) -> None:
    tester.assert_routes(
        old=None,
        new="/documentation",
        expected=["/", "documentation", "documentation/[topic]"],
        expected_modes={"documentation/[topic]": "page"},
        expected_vars={"documentation/[topic]": {"topic": None}},
    )


def test_documentation_topic_swap_only_patches_the_page(tester: RouteTester) -> None:
    res = tester.assert_routes(
        old="/documentation/routing",
        new="/documentation/testing",
        expected=["documentation/[topic]"],
        expected_vars={"documentation/[topic]": {"topic": "testing"}},
    )
    assert res.targets == [ChildContainer.ids.container("documentation")]


def test_docs_slugs_are_unique_and_loadable() -> None:
    assert len({page.slug for page in DOC_PAGES}) == len(DOC_PAGES)
    for page in DOC_PAGES:
        assert load_doc(page.slug) is not None, f"Missing docs markdown for {page.slug!r}"
