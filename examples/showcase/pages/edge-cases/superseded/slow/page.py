from dash_router import RouteConfig
from edge_helpers import case_card, edge_badge

config = RouteConfig(title="Superseded · slow · Northwind Ops")
URL = "/edge-cases/superseded/slow"


def page(data: str, **_):
    return case_card(
        "/edge-cases/superseded/slow",
        edge_badge("superseded-slow", URL),
        f"Landed: {data}. If you see this, the superseded navigation was not discarded.",
    )
