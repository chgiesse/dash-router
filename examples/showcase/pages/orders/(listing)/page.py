import math
from collections.abc import Sequence
from contextlib import suppress

import dash_mantine_components as dmc
from dash import Patch, set_props
from dash.exceptions import MissingCallbackContextException

from dash_router import Link, url_for
from data import CUSTOMERS, Order, filter_orders, simulate_latency
from ui import SkeletonColumn, feature_tags, money, rendered_badge, table_head, table_skeleton_rows

from ..models import PAGE_SIZE, OrderFilters

STATUS_COLOR = {"open": "blue", "shipped": "teal", "delayed": "orange", "returned": "grape"}
PAGE_ID = "order-page"
COUNT_ID = "order-count"
COUNT_LABEL_ID = "order-count-label"


class OrdersTable(dmc.Table):
    class ids:
        tbody = "orders-listing-tbody"

    columns = [
        SkeletonColumn("Order", width="18%", kind="id", widths=(46, 48, 44, 50, 46, 48, 44, 50, 46, 48)),
        SkeletonColumn("Customer", width="42%", kind="text", widths=("74%", "58%", "82%", "64%", "70%", "86%", "60%", "76%", "66%", "78%")),
        SkeletonColumn("Status", width="22%", kind="pill", widths=(58, 66, 72, 62, 58, 68, 64, 72, 60, 66)),
        SkeletonColumn("Total", width="18%", kind="number", align="right", widths=(64, 56, 70, 60, 68, 54, 66, 62, 72, 58)),
    ]

    def __init__(
        self,
        rows: Sequence[Order] = (),
        filters: OrderFilters | None = None,
        *,
        skeleton_rows: int = PAGE_SIZE,
    ):
        body = self.create_rows(rows, filters) if rows else table_skeleton_rows(self.columns, rows=skeleton_rows)
        super().__init__(
            [table_head(self.columns), dmc.TableTbody(body, id=self.ids.tbody)],
            highlightOnHover=True,
            verticalSpacing=6,
            layout="fixed",
            className="showcase-table",
        )

    @classmethod
    def create_rows(
        cls,
        orders: Sequence[Order],
        filters: OrderFilters | None = None,
    ) -> list[dmc.TableTr]:
        if not orders:
            return [dmc.TableTr(dmc.TableTd("No orders match.", colSpan=len(cls.columns)))]
        active_filters = filters or OrderFilters()
        return [
            dmc.TableTr(
                [
                    # `Link` marks itself active on the order's URL (and its tabs); CSS highlights the row.
                    dmc.TableTd(
                        Link(f"#{o.id}", url_for("orders/[order_id]", active_filters, order_id=o.id), className="order-link")
                    ),
                    dmc.TableTd(CUSTOMERS[o.customer_id].name),
                    dmc.TableTd(dmc.Badge(o.status.value, color=STATUS_COLOR[o.status.value], variant="light", size="sm")),
                    dmc.TableTd(money(o.total), ta="right"),
                ],
                className="order-row-enter",
            )
            for o in orders
        ]

    @classmethod
    def set_data(cls, orders: Sequence[Order], filters: OrderFilters | None = None) -> None:
        with suppress(MissingCallbackContextException):
            set_props(cls.ids.tbody, {"children": cls.create_rows(orders, filters)})

    @classmethod
    def append_data(cls, orders: Sequence[Order], filters: OrderFilters | None = None) -> None:
        patch = Patch()
        patch.extend(cls.create_rows(orders, filters))
        with suppress(MissingCallbackContextException):
            set_props(cls.ids.tbody, {"children": patch})


async def page(filters: OrderFilters, **_):
    with suppress(MissingCallbackContextException):
        set_props(PAGE_ID, {"disabled": True})

    # Frame 0: push the table shell + skeleton rows directly (no LazyContainer).
    yield dmc.Stack(
        [
            dmc.Group(
                [feature_tags("(listing) slot: generator layout", "set_data + append_data"), rendered_badge()],
                justify="space-between",
            ),
            OrdersTable(filters=filters),
        ],
        gap="xs",
    )

    await simulate_latency(1.5)
    rows = filter_orders(filters.status, filters.q)
    start = (filters.page - 1) * PAGE_SIZE
    page_rows = rows[start : start + PAGE_SIZE]
    pages = max(1, math.ceil(len(rows) / PAGE_SIZE))
    count_label = "order" if len(rows) == 1 else "orders"

    if not page_rows:
        yield OrdersTable.set_data([], filters)
    else:
        yield OrdersTable.set_data(page_rows[:1], filters)
        for row in page_rows[1:]:
            await simulate_latency(0.09)
            yield OrdersTable.append_data([row], filters)

    # Update the pagination and count that live in the parent (`orders/page.py`) after rows finish.
    with suppress(MissingCallbackContextException):
        page_props: dict[str, int | bool] = {"total": pages, "disabled": False}
        if filters.page > pages:
            page_props["value"] = pages
        set_props(PAGE_ID, page_props)
        set_props(COUNT_ID, {"value": len(rows)})
        set_props(COUNT_LABEL_ID, {"children": count_label})
    yield
