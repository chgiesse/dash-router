from dash_router import RouteConfig
from edge_helpers import case_card, edge_badge

config = RouteConfig(title="Superseded · fast · Northwind Ops")
URL = "/edge-cases/superseded/fast"


def page(**_):
    return case_card(
        "/edge-cases/superseded/fast",
        edge_badge("superseded-fast", URL),
        "Fast landed and stayed. Slow was superseded and never rendered.",
    )
