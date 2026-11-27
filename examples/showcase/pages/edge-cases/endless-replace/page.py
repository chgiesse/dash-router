import dash_mantine_components as dmc

from dash_router import RouteConfig, SlotContainer
from edge_helpers import case_card, edge_badge
from ui import link

config = RouteConfig(title="Endless replace · Northwind Ops")
URL = "/edge-cases/endless-replace"


def page(stream: SlotContainer, **_):
    return case_card(
        URL,
        edge_badge("endless-replace", URL),
        dmc.Group(
            [
                link("?mode=a", "/edge-cases/endless-replace?mode=a", size="sm"),
                link("?mode=b", "/edge-cases/endless-replace?mode=b", size="sm"),
                link("Leave to /edge-cases", "/edge-cases", size="sm"),
            ],
            gap="md",
        ),
        stream,
    )
