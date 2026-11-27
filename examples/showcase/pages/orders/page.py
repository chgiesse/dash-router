"""Orders: a master/detail layout using `page.py` + `(listing)` passive slot + `[order_id]`.

`page.py` renders with every navigation under `/orders`. Its `children` box holds `[order_id]/default.py`
(the empty state at `/orders`) or the order detail (`[order_id]/page.py`).
`(listing)` is a passive slot (always rendered next to the detail) and `[order_id]` is the child route.
The two re-render independently: filters only touch the listing, selecting an order only touches the detail.

The filter controls and the pagination live here, outside the `(listing)` lazy boundary: while
the list reloads, its `loading.py` skeleton replaces only the table, so the controls stay put.
This page does not subscribe to the filters (it reads them from `**query`, which subscribes to
nothing), so a filter change never re-renders it. Each control is wrapped in `dmc.UrlParam` to
sync with the query string directly (no clientside callback), and `(listing)/page.py` updates
the pagination's page count and total via `dash.set_props` when the new rows arrive.
"""

import dash_mantine_components as dmc
from pydantic import ValidationError

from dash_router import ChildContainer, RouteConfig, SlotContainer
from data import OrderStatus
from ui import feature_tags, rendered_badge

from .models import OrderFilters

config = RouteConfig(title="Orders · Northwind Ops")

STATUS_ID = "order-status"
SEARCH_ID = "order-search"
PAGE_ID = "order-page"
COUNT_ID = "order-count"
COUNT_LABEL_ID = "order-count-label"


def _initial_filters(query: dict) -> OrderFilters:
    try:
        return OrderFilters.model_validate({k: v for k, v in query.items() if k in OrderFilters.model_fields})
    except ValidationError:
        return OrderFilters()


def _order_list(listing: SlotContainer, filters: OrderFilters) -> dmc.Card:
    controls = dmc.Stack(
        [
            dmc.UrlParam(
                dmc.SegmentedControl(
                    id=STATUS_ID,
                    value=filters.status.value,
                    data=[s.value for s in OrderStatus],
                    size="xs",
                    fullWidth=True,
                ),
                param="status",
                default=OrderStatus.ALL.value,
                clear=["page"],
                twoWay=True,
            ),
            dmc.UrlParam(
                dmc.TextInput(
                    id=SEARCH_ID,
                    value=filters.q,
                    placeholder="Search order # or customer…",
                    debounce=400,
                    size="xs",
                ),
                param="q",
                default="",
                clear=["page"],
                twoWay=True,
            ),
        ],
        gap="xs",
    )
    pager = dmc.Group(
        [
            dmc.Group(
                [
                    dmc.RollingNumber(id=COUNT_ID, value=0, thousandSeparator=True, fz="xs", c="dimmed"),
                    dmc.Text("orders", id=COUNT_LABEL_ID, size="xs", c="dimmed"),
                ],
                gap=4,
            ),
            dmc.UrlParam(
                dmc.Pagination(
                    id=PAGE_ID,
                    total=max(filters.page, 1),
                    value=filters.page,
                    size="xs",
                    siblings=1,
                    boundaries=1,
                    disabled=True,
                ),
                param="page",
                format="number",
                default=1,
                twoWay=True,
            ),
        ],
        justify="space-between",
        wrap="nowrap",
    )
    return dmc.Card(
        dmc.Stack(
            [
                dmc.Stack(
                    [dmc.Text("Order list", fw=600), feature_tags("controls in orders/page.py", "dmc.UrlParam (no callback)")],
                    gap=4,
                ),
                controls,
                dmc.ScrollArea(listing, h=560),
                pager,
            ],
            gap="sm",
        ),
        withBorder=True,
        radius="md",
        padding="md",
    )


def page(children: ChildContainer, listing: SlotContainer, **query):
    return dmc.Stack(
        [
            dmc.Group(
                [
                    dmc.Stack(
                        [
                            dmc.Title("Orders", order=2),
                            feature_tags("passive slot + child route", "Pydantic query model"),
                        ],
                        gap=4,
                    ),
                    rendered_badge("page rendered"),
                ],
                justify="space-between",
                align="flex-start",
            ),
            dmc.Grid(
                [
                    dmc.GridCol(_order_list(listing, _initial_filters(query)), span={"base": 12, "lg": 5}),
                    dmc.GridCol(dmc.Box(children, mih=490), span={"base": 12, "lg": 7}),
                ],
            ),
        ]
    )
