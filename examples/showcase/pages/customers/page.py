"""Customers: parallel routes.

Next to the main child route, two `(slots)` define their *own* routes:

- `(inspector)` matches `accounts/[customer_id]` and falls back to `default.py` elsewhere.
- `(pinned)` matches `accounts/[customer_id]`, `directory` and `segments` but has no
  `default.py`: on `/customers/insights` it renders empty. Nothing is retained across navigations,
  so a soft navigation and a hard load of that URL behave the same way.

Every branch receives its own copy of the URL cursor, so `customer_id` is parsed independently
by the main route and by each slot.
"""

import dash_mantine_components as dmc

from dash_router import ChildContainer, RouteConfig, SlotContainer
from ui import feature_tags, link, rendered_badge

config = RouteConfig(default_child="directory", title="Customers · Northwind Ops")

TABS = [("Directory", "/customers/directory"), ("Segments", "/customers/segments"), ("Insights", "/customers/insights")]


def page(children: ChildContainer, inspector: SlotContainer, pinned: SlotContainer, **_):
    return dmc.Stack(
        [
            dmc.Group(
                [
                    dmc.Stack(
                        [
                            dmc.Title("Customers", order=2),
                            feature_tags("parallel routes in (slots)", "default.py", "no retention"),
                        ],
                        gap=4,
                    ),
                    rendered_badge("page rendered"),
                ],
                justify="space-between",
                align="flex-start",
            ),
            dmc.Group([link(label, href) for label, href in TABS], gap="lg"),
            dmc.Grid(
                [
                    dmc.GridCol(dmc.Box(children, mih=620), span={"base": 12, "lg": 7}),
                    dmc.GridCol(dmc.Stack([dmc.Box(inspector, mih=195), dmc.Box(pinned, mih=180)]), span={"base": 12, "lg": 5}),
                ]
            ),
        ]
    )
