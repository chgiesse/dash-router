import dash_mantine_components as dmc

from dash_router import ChildContainer, RouteConfig
from edge_helpers import case_card, edge_badge
from ui import link

config = RouteConfig(default_child="tab-a", title="Parent loading · Northwind Ops")
URL = "/edge-cases/parent-loading"


def page(children: ChildContainer, data: dict[str, bool], **_):
    return case_card(
        URL,
        edge_badge("parent-loading", URL),
        dmc.Group(
            [
                link("Tab A", "/edge-cases/parent-loading/tab-a", size="sm"),
                link("Tab B", "/edge-cases/parent-loading/tab-b", size="sm"),
            ],
            gap="md",
        ),
        children,
    )
