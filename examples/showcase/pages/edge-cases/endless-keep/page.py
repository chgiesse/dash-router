import dash_mantine_components as dmc

from dash_router import RouteConfig, SlotContainer
from edge_helpers import case_card, edge_badge
from ui import link

config = RouteConfig(title="Endless keep · Northwind Ops")
URL = "/edge-cases/endless-keep"


def page(feed: SlotContainer, panel: SlotContainer, **_):
    return case_card(
        URL,
        edge_badge("endless-keep", URL),
        dmc.Group(
            [
                link("?panel=a", "/edge-cases/endless-keep", size="sm"),
                link("?panel=b", "/edge-cases/endless-keep?panel=b", size="sm"),
            ],
            gap="md",
        ),
        dmc.SimpleGrid([feed, panel], cols=2),
    )
