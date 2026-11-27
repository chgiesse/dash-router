import dash_mantine_components as dmc

from dash_router import ChildContainer, RouteConfig
from edge_helpers import case_card, edge_badge
from ui import link

config = RouteConfig(default_child="one", title="Nested lazy · Northwind Ops")
URL = "/edge-cases/nested-lazy"


def page(children: ChildContainer, data: str, **_):
    return case_card(
        URL,
        edge_badge("nested-lazy", URL),
        dmc.Group(
            [
                link("one (inner api 1.5 s)", "/edge-cases/nested-lazy/one", size="sm"),
                link("two", "/edge-cases/nested-lazy/two", size="sm"),
            ],
            gap="md",
        ),
        dmc.Text(f"outer api: {data}", size="xs", c="dimmed"),
        children,
    )
