import dash_mantine_components as dmc

from dash_router import RouteConfig, SlotContainer
from edge_helpers import case_card, edge_badge
from ui import link

config = RouteConfig(title="Sibling lazy · Northwind Ops")


def page(left: SlotContainer, right: SlotContainer, **_):
    return case_card(
        "/edge-cases/sibling-lazy",
        edge_badge("sibling-lazy", "/edge-cases/sibling-lazy"),
        dmc.Group(
            [
                link("?tag=a", "/edge-cases/sibling-lazy?tag=a", size="sm"),
                link("?tag=b", "/edge-cases/sibling-lazy?tag=b", size="sm"),
            ],
            gap="md",
        ),
        dmc.SimpleGrid([left, right], cols=2),
    )
