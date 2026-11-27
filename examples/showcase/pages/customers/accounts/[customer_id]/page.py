import dash_mantine_components as dmc

from dash_router import RouteConfig, url_for
from ui import SkeletonColumn, link, money, section, table_head

config = RouteConfig(title="Customer · Northwind Ops")
_COLUMNS = [
    SkeletonColumn("Order", width="18%"),
    SkeletonColumn("Placed", width="30%"),
    SkeletonColumn("Status", width="26%"),
    SkeletonColumn("Total", width="26%", align="right"),
]


def page(data: dict, customer_id: int, **_):
    customer, orders = data["customer"], data["orders"]
    rows = [
        dmc.TableTr(
            [
                dmc.TableTd(link(f"#{o.id}", url_for("orders/[order_id]", order_id=o.id))),
                dmc.TableTd(o.placed.isoformat()),
                dmc.TableTd(o.status.value),
                dmc.TableTd(money(o.total), ta="right"),
            ]
        )
        for o in orders
    ]
    return section(
        customer.name,
        dmc.Stack(
            [
                dmc.Text(f"{customer.city} · {customer.segment} · lifetime value {money(customer.lifetime_value)}", size="sm", c="dimmed"),
                dmc.Table(
                    [
                        table_head(_COLUMNS),
                        dmc.TableTbody(rows or [dmc.TableTr(dmc.TableTd("No orders yet.", colSpan=4))]),
                    ],
                    verticalSpacing=6,
                    layout="fixed",
                    className="showcase-table",
                ),
                dmc.Group(
                    [
                        link("← previous", url_for("customers/accounts/[customer_id]", customer_id=max(1, customer_id - 1)), size="sm"),
                        link("next →", url_for("customers/accounts/[customer_id]", customer_id=min(20, customer_id + 1)), size="sm"),
                    ],
                    justify="space-between",
                ),
            ]
        ),
        features=("main branch: accounts/[customer_id]",),
    )
