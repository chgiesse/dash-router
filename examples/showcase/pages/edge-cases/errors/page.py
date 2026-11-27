import dash_mantine_components as dmc

from dash_router import SlotContainer
from edge_helpers import case_card, edge_badge

URL = "/edge-cases/errors"


def page(**slots: SlotContainer):
    return case_card(
        URL,
        edge_badge("errors", URL),
        dmc.SimpleGrid([slots["api-err"], slots["gen-err"]], cols=2),
    )
