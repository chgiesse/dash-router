import dash_mantine_components as dmc

from dash_router import ChildContainer, RouteConfig
from edge_helpers import case_card, edge_badge
from ui import link

config = RouteConfig(default_child="slow", title="Lazy replaced · Northwind Ops")
URL = "/edge-cases/lazy-replaced"


def page(children: ChildContainer, **_):
    return case_card(
        URL,
        edge_badge("lazy-replaced", URL),
        dmc.Group(
            [
                link("Slow (lazy, 3.0 s)", "/edge-cases/lazy-replaced/slow", size="sm"),
                link("Other", "/edge-cases/lazy-replaced/other", size="sm"),
            ],
            gap="md",
        ),
        children,
    )
