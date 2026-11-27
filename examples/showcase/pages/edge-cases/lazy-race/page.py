import dash_mantine_components as dmc

from dash_router import ChildContainer, RouteConfig, SlotContainer
from edge_helpers import case_card, edge_badge
from ui import link

config = RouteConfig(title="Lazy race · Northwind Ops")
URL = "/edge-cases/lazy-race"


def page(children: ChildContainer, lazy: SlotContainer, **_):
    return case_card(
        URL,
        edge_badge("lazy-race", URL),
        dmc.Group([link("Next (api.py 1.5 s)", "/edge-cases/lazy-race/next", size="sm")], gap="md"),
        lazy,
        children,
    )
