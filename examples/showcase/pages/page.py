"""Root shell: accepts `children`, so the router mounts it once and only patches its child."""

import random

import dash_mantine_components as dmc
from dash import Input, callback

from code_viewer import CODE_BUTTON_ID, code_drawer
from dash_router import ChildContainer, RouteConfig, navigate, url_for
from data import ORDERS
from ui import rendered_badge

config = RouteConfig(default_child="overview", title="Northwind Ops")

NAV = [
    ("Overview", "/overview", "Parallel slots, streaming, errors"),
    ("Orders", "/orders", "Master/detail, query models"),
    ("Customers", "/customers", "Parallel routes, default & empty slots"),
    ("Knowledge base", "/docs", "Catch-all routes"),
    ("Status wall", "/status", "Standalone route"),
    ("Settings", "/settings", "navigate() from a callback"),
    ("Documentation", "/documentation", "Every feature explained"),
    ("Edge cases", "/edge-cases", "Races, streams, fallbacks"),
]


def page(children: ChildContainer, **_):
    navbar = dmc.Stack(
        [
            # `active="partial"` follows the router's location, so the never re-rendered shell stays in sync.
            dmc.NavLink(label=label, description=desc, href=href, active="partial", variant="filled")
            for label, href, desc in NAV
        ],
        gap=4,
    )
    header = dmc.Group(
        [
            dmc.Group(
                [
                    dmc.Title("Northwind Ops", order=3),
                    dmc.Badge("dash_router showcase", variant="light"),
                ],
                gap="sm",
            ),
            dmc.Group(
                [
                    dmc.Button(
                        "Open a random order",
                        id="random-order",
                        variant="light",
                        size="xs",
                    ),
                    dmc.Button(
                        "View code for this page",
                        id=CODE_BUTTON_ID,
                        variant="filled",
                        size="xs",
                    ),
                    rendered_badge("shell rendered"),
                ],
                gap="sm",
            ),
        ],
        justify="space-between",
        h="100%",
        px="md",
    )
    return dmc.AppShell(
        [
            dmc.AppShellHeader(header),
            dmc.AppShellNavbar(navbar, p="sm"),
            dmc.AppShellMain(children),
            code_drawer(),
        ],
        header={"height": 56},
        navbar={"width": 240, "breakpoint": "sm"},
        padding="md",
    )


@callback(Input("random-order", "n_clicks"), prevent_initial_call=True)
def open_random_order(n_clicks: int | None) -> None:
    if not n_clicks:
        return
    # `navigate` + `url_for`: programmatic navigation from any server callback.
    navigate(url_for("orders/[order_id]", order_id=random.choice(list(ORDERS))))

