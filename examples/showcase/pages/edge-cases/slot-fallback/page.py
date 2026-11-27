import dash_mantine_components as dmc

from dash_router import ChildContainer, RouteConfig, SlotContainer
from edge_helpers import edge_badge
from ui import link

config = RouteConfig(title="Slot fallback · Northwind Ops")


def page(children: ChildContainer, **slots: SlotContainer):
    return dmc.Stack(
        [
            dmc.Group(
                [
                    link("/matched", "/edge-cases/slot-fallback/matched", size="sm"),
                    link("/other", "/edge-cases/slot-fallback/other", size="sm"),
                ],
                gap="md",
            ),
            edge_badge("slot-fallback", "/edge-cases/slot-fallback"),
            dmc.SimpleGrid([slots["with-default"], slots["no-default"]], cols=2),
            children,
        ],
        gap="sm",
    )
