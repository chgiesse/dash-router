import dash_mantine_components as dmc
from dash import Input, callback

from dash_router import navigate
from edge_helpers import case_card, edge_badge

URL = "/edge-cases/same-url"


def page(**_):
    return case_card(
        URL,
        edge_badge("same-url", URL),
        dmc.Button("Server navigate() to this URL", id="same-url-button", variant="light", size="sm"),
        dmc.Text("The render counter in the badge must not change after the click.", size="xs", c="dimmed"),
    )


@callback(Input("same-url-button", "n_clicks"), prevent_initial_call=True)
def navigate_to_same_url(n_clicks: int | None) -> None:
    if n_clicks:
        navigate(URL)
