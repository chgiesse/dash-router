"""Wall display: `is_static=True` mounts straight into the root container, without the shell."""

from pathlib import Path

import dash_mantine_components as dmc

from code_viewer import source_block
from dash_router import RouteConfig
from data import ORDERS, OrderStatus
from ui import feature_tags, rendered_badge

config = RouteConfig(is_static=True, title="Status wall · Northwind Ops")


def _tile(label: str, value: int, color: str) -> dmc.Paper:
    return dmc.Paper(
        [dmc.Text(label, c="dimmed", tt="uppercase", fw=700), dmc.Title(str(value), order=1, c=color, fz=72)],
        p="xl",
        withBorder=True,
        ta="center",
    )


def page(**_):
    counts = {s: sum(o.status is s for o in ORDERS.values()) for s in OrderStatus if s is not OrderStatus.ALL}
    return dmc.Container(
        dmc.Stack(
            [
                dmc.Group(
                    [
                        dmc.Stack([dmc.Title("Fulfilment status", order=1), feature_tags("is_static=True", "no shell")], gap=4),
                        dmc.Group([rendered_badge(), dmc.Anchor("Exit wall display", href="/overview")]),
                    ],
                    justify="space-between",
                ),
                dmc.SimpleGrid(
                    [
                        _tile("Open", counts[OrderStatus.OPEN], "blue"),
                        _tile("Shipped", counts[OrderStatus.SHIPPED], "teal"),
                        _tile("Delayed", counts[OrderStatus.DELAYED], "orange"),
                        _tile("Returned", counts[OrderStatus.RETURNED], "grape"),
                    ],
                    cols={"base": 2, "lg": 4},
                ),
                dmc.Spoiler(
                    showLabel="Show the code of this page",
                    hideLabel="Hide code",
                    maxHeight=0,
                    children=source_block(Path(__file__)),
                ),
            ],
            gap="xl",
            py="xl",
        ),
        size="xl",
    )
