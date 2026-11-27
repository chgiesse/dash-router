import dash_mantine_components as dmc

from dash_router import url_for
from ui import SkeletonColumn, link, section, table_head

STATUS_COLOR = {"open": "blue", "shipped": "teal", "delayed": "orange", "returned": "grape"}
_COLUMNS = [
    SkeletonColumn("Order", width="18%"),
    SkeletonColumn("Customer", width="44%"),
    SkeletonColumn("Status", width="18%"),
    SkeletonColumn("Placed", width="20%"),
]


def page(data: list[dict], **_):
    rows = [
        dmc.TableTr(
            [
                dmc.TableTd(link(f"#{row['order']}", url_for("orders/[order_id]", order_id=row["order"]))),
                dmc.TableTd(row["customer"]),
                dmc.TableTd(dmc.Badge(row["status"], color=STATUS_COLOR[row["status"]], variant="light")),
                dmc.TableTd(row["placed"]),
            ]
        )
        for row in data
    ]
    return section(
        "Recent activity · (activity)/api.py ≈ 3.5 s",
        dmc.Stack(
            [
                dmc.Table(
                    [
                        table_head(_COLUMNS),
                        dmc.TableTbody(rows),
                    ],
                    highlightOnHover=True,
                    layout="fixed",
                    className="showcase-table",
                ),
                dmc.Group(
                    [
                        dmc.Text("Want to see an error boundary?", size="sm", c="dimmed"),
                        link("Make this slot fail", "/overview?fail=activity", size="sm"),
                    ],
                    gap="xs",
                ),
            ]
        ),
        features=("slowest slot", "error.py boundary"),
    )
