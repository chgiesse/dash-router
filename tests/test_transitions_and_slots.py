import pytest

from dash_router import ChildContainer, RootContainer, RouteTester, SlotContainer, assert_transition
from dash_router.components import ContainerId, container_key
from dash_router.types import RenderMode


def test_tickets_nested_slots_and_incremental_transitions():
    tester = RouteTester.from_spec(
        {
            "tickets": {
                "[ticket_id]": {
                    "(detail)": {
                        "(summary)": {},
                    },
                    "(activity)": {
                        "inputs": ["filter"],
                        "(comments)": {},
                    },
                },
            },
        }
    )

    # 1. Initial hard load on /tickets (omitted [ticket_id] -> ticket_id=None, stops before per-ticket slots)
    res_root = tester.assert_routes(
        old=None,
        new="/tickets",
        expected=["tickets", "tickets/[ticket_id]"],
        expected_vars={"tickets/[ticket_id]": {"ticket_id": None}},
    )
    assert res_root.targets == [RootContainer.ids.container]

    # 2. /tickets -> /tickets/1001: `tickets` stays mounted; ChildContainer("tickets") renders [ticket_id] + all nested slots
    res_1001 = tester.assert_routes(
        old="/tickets",
        new="/tickets/1001",
        expected=[
            "tickets/[ticket_id]",
            "tickets/[ticket_id]/(detail)",
            "tickets/[ticket_id]/(detail)/(summary)",
            "tickets/[ticket_id]/(activity)",
            "tickets/[ticket_id]/(activity)/(comments)",
        ],
        expected_vars={
            "tickets/[ticket_id]": {"ticket_id": "1001"},
            "tickets/[ticket_id]/(detail)/(summary)": {"ticket_id": "1001"},
        },
    )
    assert res_1001.targets == [ChildContainer.ids.container("tickets")]

    # 3. /tickets/1001 -> /tickets/1002: switches ticket_id, keeping `tickets` shell mounted
    tester.assert_routes(
        old="/tickets/1001",
        new="/tickets/1002",
        expected=[
            "tickets/[ticket_id]",
            "tickets/[ticket_id]/(detail)",
            "tickets/[ticket_id]/(detail)/(summary)",
            "tickets/[ticket_id]/(activity)",
            "tickets/[ticket_id]/(activity)/(comments)",
        ],
        expected_vars={"tickets/[ticket_id]": {"ticket_id": "1002"}},
    )

    # 4. Query-only update subscribed ONLY by `(activity)`: `tickets`, `[ticket_id]`, and `(detail)` stay untouched!
    res_filter = tester.assert_routes(
        old="/tickets/1002",
        new="/tickets/1002?filter=unread",
        expected=[
            "tickets/[ticket_id]/(activity)",
            "tickets/[ticket_id]/(activity)/(comments)",
        ],
    )
    assert res_filter.targets == [SlotContainer.ids.container("tickets/[ticket_id]", "activity")]


def test_no_sibling_path_var_leakage_into_passive_slots():
    tester = RouteTester.from_spec(
        {
            "sales": {
                "invoices": {
                    "(overview)": {},
                    "[invoice_id]": {
                        "default_child": "items",
                        "items": {},
                        "positions": {},
                    },
                },
            },
        }
    )

    # Initial load of /sales/invoices/1001/items:
    # `(overview)` is a sibling of `[invoice_id]` and MUST NOT receive `invoice_id="1001"`!
    res = tester.assert_routes(
        old=None,
        new="/sales/invoices/1001/items",
        expected=[
            "sales",
            "sales/invoices",
            "sales/invoices/(overview)",
            "sales/invoices/[invoice_id]",
            "sales/invoices/[invoice_id]/items",
        ],
    )
    assert "invoice_id" not in res.vars_for("sales/invoices/(overview)")
    assert res.vars_for("sales/invoices/[invoice_id]")["invoice_id"] == "1001"
    assert res.vars_for("sales/invoices/[invoice_id]/items")["invoice_id"] == "1001"

    # Switching from invoice 1001 -> 1002 MUST NOT re-render `(overview)`!
    tester.assert_routes(
        old="/sales/invoices/1001/items",
        new="/sales/invoices/1002/items",
        expected=[
            "sales/invoices/[invoice_id]",
            "sales/invoices/[invoice_id]/items",
        ],
    )

    # Switching child tab items -> positions on same invoice 1002 ONLY renders `positions`!
    res_tab = tester.assert_routes(
        old="/sales/invoices/1002/items",
        new="/sales/invoices/1002/positions",
        expected=["sales/invoices/[invoice_id]/positions"],
    )
    assert res_tab.targets == [ChildContainer.ids.container("sales/invoices/[invoice_id]")]


def test_parallel_routes_in_slots_with_default_fallback():
    tester = RouteTester.from_spec(
        {
            "workspace": {
                "settings": {},
                "billing": {},
                "projects": {
                    "[project_id]": {},
                },
                "(inspector)": {
                    "default": True,
                    "settings": {},
                    "projects": {
                        "[project_id]": {},
                    },
                },
            },
        }
    )

    # 1. Both main branch and `(inspector)` slot match literal `settings` in parallel
    tester.assert_routes(
        old=None,
        new="/workspace/settings",
        expected=[
            "workspace",
            "workspace/settings",
            "workspace/(inspector)",
            "workspace/(inspector)/settings",
        ],
    )

    # 2. Both main branch and `(inspector)` slot independently consume `projects/[project_id]` = "alpha"!
    #    Notice `workspace` and `workspace/(inspector)` wrapper stay mounted — only their ChildContainers update!
    res_alpha = tester.assert_routes(
        old="/workspace/settings",
        new="/workspace/projects/alpha",
        expected=[
            "workspace/projects",
            "workspace/projects/[project_id]",
            "workspace/(inspector)/projects",
            "workspace/(inspector)/projects/[project_id]",
        ],
        expected_vars={
            "workspace/projects/[project_id]": {"project_id": "alpha"},
            "workspace/(inspector)/projects/[project_id]": {"project_id": "alpha"},
        },
    )
    assert res_alpha.targets == [
        ChildContainer.ids.container("workspace"),
        ChildContainer.ids.container("workspace/(inspector)"),
    ]

    # 3. Switching project_id `alpha` -> `beta` keeps BOTH `workspace/projects` AND `workspace/(inspector)/projects` mounted!
    res_beta = tester.assert_routes(
        old="/workspace/projects/alpha",
        new="/workspace/projects/beta",
        expected=[
            "workspace/projects/[project_id]",
            "workspace/(inspector)/projects/[project_id]",
        ],
        expected_vars={
            "workspace/projects/[project_id]": {"project_id": "beta"},
            "workspace/(inspector)/projects/[project_id]": {"project_id": "beta"},
        },
    )
    assert res_beta.targets == [
        ChildContainer.ids.container("workspace/projects"),
        ChildContainer.ids.container("workspace/(inspector)/projects"),
    ]

    # 4. Navigate to `/workspace/billing` (defined in main branch, NOT in `(inspector)`):
    #    `(inspector)` switches to `default.py` (`mode="default"`)!
    res_billing = tester.assert_routes(
        old="/workspace/projects/beta",
        new="/workspace/billing",
        expected=[
            "workspace/billing",
            "workspace/(inspector)",
        ],
        expected_modes={
            "workspace/billing": "page",
            "workspace/(inspector)": "default",
        },
    )
    assert res_billing.targets == [
        ChildContainer.ids.container("workspace"),
        SlotContainer.ids.container("workspace", "inspector"),
    ]

    # 4. Completely unknown segment `/workspace/unknown/deep` still 404s (default.py doesn't swallow invalid URLs)
    unmatched = tester.transition(old="/workspace/billing", new="/workspace/unknown/deep")
    assert not unmatched.matched


def test_unmatched_parallel_slot_without_default_renders_empty():
    tester = RouteTester.from_spec(
        {
            "other": {},
            "workspace": {
                "settings": {},
                "billing": {},
                "audit": {},
                "(inspector)": {
                    # No `default` layout!
                    "settings": {},
                },
            },
        }
    )

    # 1. Hard navigation to `/workspace/billing`: `(inspector)` has no match and no `default.py`, so it renders empty.
    tester.assert_routes(
        old=None,
        new="/workspace/billing",
        expected=["workspace", "workspace/billing"],
        expected_modes={"workspace/(inspector)": "empty"},
    )

    # 2. Cross-branch navigation from `/other` behaves the same way.
    tester.assert_routes(
        old="/other",
        new="/workspace/billing",
        expected=["workspace", "workspace/billing"],
        expected_modes={"workspace/(inspector)": "empty"},
    )

    # 3. Soft navigation from `/workspace/settings` -> `/workspace/billing` swaps `(inspector)` to empty.
    res_empty = tester.assert_routes(
        old="/workspace/settings",
        new="/workspace/billing",
        expected=["workspace/billing"],
        expected_modes={"workspace/billing": "page", "workspace/(inspector)": "empty"},
    )
    assert res_empty.targets == [
        ChildContainer.ids.container("workspace"),
        SlotContainer.ids.container("workspace", "inspector"),
    ]

    # 4. Multi-hop soft navigation `/workspace/billing` -> `/workspace/audit` keeps `(inspector)` empty, so it isn't patched.
    res_audit = tester.assert_routes(
        old="/workspace/billing",
        new="/workspace/audit",
        expected=["workspace/audit"],
    )
    assert res_audit.targets == [ChildContainer.ids.container("workspace")]

    # 5. Matching `(inspector)` again transitions back to `page`, rendering its `settings` route.
    tester.assert_routes(
        old="/workspace/audit",
        new="/workspace/settings",
        expected=["workspace/settings", "workspace/(inspector)", "workspace/(inspector)/settings"],
        expected_modes={"workspace/(inspector)": "page"},
    )


def test_slot_only_subnavigation_without_main_children():
    tester = RouteTester.from_spec(
        {
            "dashboard": {
                "(left)": {
                    "overview": {},
                    "metrics": {},
                },
                "(right)": {},
            },
        }
    )

    tester.assert_routes(
        old=None,
        new="/dashboard/overview",
        expected=[
            "dashboard",
            "dashboard/(left)",
            "dashboard/(left)/overview",
            "dashboard/(right)",
        ],
    )

    # Navigating `/dashboard/overview` -> `/dashboard/metrics` ONLY updates `(left)`'s child container!
    res = tester.assert_routes(
        old="/dashboard/overview",
        new="/dashboard/metrics",
        expected=["dashboard/(left)/metrics"],
    )
    assert res.targets == [ChildContainer.ids.container("dashboard/(left)")]


@pytest.mark.parametrize(
    ("old_url", "new_url", "expected_segments", "expected_rest", "expected_mode"),
    [
        (
            "/projects/alpha",
            "/projects/alpha/files",
            ["projects/[team_id]/files", "projects/[team_id]/files/[__rest]"],
            [],
            "default",
        ),
        (
            "/projects/alpha/files",
            "/projects/alpha/files/docs",
            ["projects/[team_id]/files/[__rest]"],
            ["docs"],
            "page",
        ),
        (
            "/projects/alpha/files/docs",
            "/projects/alpha/files/docs/2026/q4.pdf",
            ["projects/[team_id]/files/[__rest]"],
            ["docs", "2026", "q4.pdf"],
            "page",
        ),
    ],
)
def test_catch_all_transitions_and_default_mode(
    old_url: str,
    new_url: str,
    expected_segments: list[str],
    expected_rest: list[str],
    expected_mode: RenderMode,
):
    tree_spec = {
        "projects": {
            "[team_id]": {
                "files": {
                    "[__rest]": {
                        "default": True,
                    },
                },
            },
        },
    }
    tester = RouteTester.from_spec(tree_spec)
    assert_transition(
        tester,
        old=old_url,
        new=new_url,
        expected=expected_segments,
        expected_vars={
            "projects/[team_id]/files/[__rest]": {
                "team_id": "alpha",
                "rest": expected_rest,
            }
        },
        expected_modes={"projects/[team_id]/files/[__rest]": expected_mode},
    )


def test_persistent_root_shell_vs_static_routes():
    tester = RouteTester.from_spec(
        {
            "/": {"accepts_children": True},
            "login": {"is_static": True},
            "monitoring/[cid]/[unit]": {"is_static": True},
            "sales": {
                "overview": {},
            },
        }
    )

    # `/` renders persistent root shell
    tester.assert_routes(old=None, new="/", expected=["/"])

    # `/` -> `/sales/overview` keeps `/` shell mounted and patches ChildContainer("/")!
    res = tester.assert_routes(
        old="/",
        new="/sales/overview",
        expected=["sales", "sales/overview"],
    )
    assert res.targets == [ChildContainer.ids.container("/")]

    # Navigating to `is_static=True` route `/login` mounts directly into RootContainer, bypassing `/` shell
    res_login = tester.assert_routes(
        old="/sales/overview",
        new="/login",
        expected=["login"],
    )
    assert res_login.targets == [RootContainer.ids.container]

    # Multi-param static route
    tester.assert_routes(
        old="/login",
        new="/monitoring/acme/emea",
        expected=["monitoring/[cid]/[unit]"],
        expected_vars={"monitoring/[cid]/[unit]": {"cid": "acme", "unit": "emea"}},
    )


def test_unsubscribed_query_change_patches_nothing():
    from dash_router import DashRouter

    router = DashRouter.from_spec({"tickets": {"(list)": {"inputs": ["page"]}, "[ticket_id]": {}}})
    assert router.plan("/tickets/7", "/tickets/7?unrelated=1").patches == []
    assert router.plan("/tickets/7", "/tickets/7?page=2").targets == [SlotContainer.ids.container("tickets", "list")]


def _keys(*containers: ContainerId) -> set[str]:
    return {container_key(container) for container in containers}


def test_resolve_targets_lifts_missing_child_container_to_its_owner():
    from dash_router import DashRouter
    from dash_router.core.matcher import resolve_targets

    router = DashRouter.from_spec({"orders": {"(list)": {}, "[order_id]": {}}})
    plan = router.plan("/orders/1", "/orders/2")
    assert plan.targets == [ChildContainer.ids.container("orders")]

    # `orders` is still showing its loading skeleton, so `orders-children` is not mounted yet.
    patches = resolve_targets(plan, _keys(RootContainer.ids.container, SlotContainer.ids.container("orders", "list")))
    assert [p.target.container_id for p in patches] == [RootContainer.ids.container]
    assert patches[0].subtree is not None
    assert patches[0].subtree.node_id == "orders"

    # Once the child container is mounted the patch targets it directly.
    patches = resolve_targets(plan, _keys(RootContainer.ids.container, ChildContainer.ids.container("orders")))
    assert [p.target.container_id for p in patches] == [ChildContainer.ids.container("orders")]


def test_resolve_targets_lifts_a_missing_chain_all_the_way_to_root():
    from dash_router import DashRouter
    from dash_router.core.matcher import resolve_targets

    router = DashRouter.from_spec({"shop": {"orders": {"[order_id]": {"items": {}}}}})
    plan = router.plan("/shop/orders/1/items", "/shop/orders/2/items")
    assert plan.targets == [ChildContainer.ids.container("shop/orders")]

    # Neither `shop-children` nor `shop/orders-children` is mounted: the patch climbs to the root.
    patches = resolve_targets(plan, _keys(RootContainer.ids.container))
    assert [p.target.container_id for p in patches] == [RootContainer.ids.container]
    assert patches[0].subtree is not None
    assert patches[0].subtree.node_id == "shop"


def test_resolve_targets_drops_patches_covered_by_a_lifted_subtree():
    from dash_router import DashRouter
    from dash_router.core.matcher import resolve_targets

    router = DashRouter.from_spec(
        {
            "/": {
                "accepts_children": True,
                "(badge)": {"inputs": ["n"]},
            },
            "shop": {
                "(side)": {"inputs": ["tab"]},
                "orders": {"[order_id]": {}},
            },
        }
    )
    plan = router.plan("/shop/orders/1?tab=a&n=1", "/shop/orders/2?tab=b&n=2")
    assert {container_key(target) for target in plan.targets} == _keys(
        SlotContainer.ids.container("shop", "side"),
        ChildContainer.ids.container("shop/orders"),
        SlotContainer.ids.container("/", "badge"),
    )

    # `shop-children` and `shop/orders-children` are missing, so the orders patch lifts to `/-children` with `shop`.
    # That re-renders `(side)` inside `shop`, so its own patch is dropped. The unrelated `(badge)` stays.
    mounted = _keys(
        ChildContainer.ids.container("/"),
        SlotContainer.ids.container("/", "badge"),
        SlotContainer.ids.container("shop", "side"),
    )
    patches = resolve_targets(plan, mounted)
    assert [p.target.container_id for p in patches] == [
        ChildContainer.ids.container("/"),
        SlotContainer.ids.container("/", "badge"),
    ]
    assert patches[0].subtree is not None
    assert patches[0].subtree.node_id == "shop"


def test_literal_prefix_falls_back_to_dynamic_sibling():
    tester = RouteTester.from_spec({"x": {"new": {}, "[id]": {"edit": {}}}})

    tester.assert_routes(None, "/x/new", expected=["x", "x/new"])
    res_new_edit = tester.assert_routes(
        None,
        "/x/new/edit",
        expected=["x", "x/[id]", "x/[id]/edit"],
    )
    assert res_new_edit.plan.node_vars["x/[id]/edit"]["id"] == "new"

    res_num_edit = tester.assert_routes(
        None,
        "/x/5/edit",
        expected=["x", "x/[id]", "x/[id]/edit"],
    )
    assert res_num_edit.plan.node_vars["x/[id]/edit"]["id"] == "5"
