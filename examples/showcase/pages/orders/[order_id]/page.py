"""Order detail: `[order_id]/page.py` renders at once, with `default_child="summary"`.

The header comes from `ORDERS` directly, so it never waits. The tab bar is a `UrlSegment`: the active tab is the
URL segment after `/orders/<id>`, `summary` is the default (`default_child="summary"`) and the bare URL stands for it.
Clicking a tab pushes its URL, and back/forward select the tab again, with no callback. The children box holds
`summary/` (at `/orders/<id>` or `/orders/<id>/summary`), `timeline/`, or `notes/`.
"""

import dash_mantine_components as dmc

from dash_router import ChildContainer, RouteConfig, UrlSegment
from data import CUSTOMERS, ORDERS
from ui import feature_tags, money, rendered_badge

from .tabs import order_tabs

config = RouteConfig(default_child="summary")


def page(children: ChildContainer, order_id: int, **_):
    order = ORDERS.get(order_id)
    if order is None:
        raise LookupError(f"Order #{order_id} does not exist")
    customer = CUSTOMERS[order.customer_id]
    return dmc.Card(
        [
            dmc.Group(
                [
                    dmc.Stack(
                        [
                            dmc.Title(f"Order #{order.id} · {money(order.total)}", order=3),
                            dmc.Text(f"{customer.name} · {customer.city}", c="dimmed", size="sm"),
                            feature_tags("default_child=summary", "UrlSegment(default=summary)"),
                        ],
                        gap=4,
                    ),
                    rendered_badge("page rendered"),
                ],
                justify="space-between",
                align="flex-start",
            ),
            UrlSegment(order_tabs(), children, default="summary"),
            dmc.Box(children, pt="md", mih=290),
        ],
        withBorder=True,
        mih=490,
    )
