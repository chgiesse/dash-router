"""Plain Dash callback (not a router callback) racing two triggers.

The slow callback's `set_props` runs after the fast one's. The fast result must still win.
"""

import dash_mantine_components as dmc
from dash import Input, Output, callback, ctx, html, set_props

from dash_router import RouteConfig
from edge_helpers import case_card, edge_badge, edge_sleep

config = RouteConfig(title="Plain set_props · Northwind Ops")
URL = "/edge-cases/plain-set-props"


def page(**_):
    return case_card(
        URL,
        edge_badge("plain-set-props", URL),
        dmc.Group(
            [
                dmc.Button("Slow plain (2s)", id="plain-slow", variant="light", size="sm"),
                dmc.Button("Fast plain (0.1s)", id="plain-fast", variant="light", size="sm"),
            ],
            gap="md",
        ),
        dmc.Text("Output:", size="xs", c="dimmed"),
        html.Div(id="edge-plain-out"),
        dmc.Text("set_props side channel:", size="xs", c="dimmed"),
        html.Div(id="edge-plain-side"),
    )


@callback(
    Output("edge-plain-out", "children"),
    Input("plain-slow", "n_clicks"),
    Input("plain-fast", "n_clicks"),
    prevent_initial_call=True,
)
async def plain_click(*_: int | None) -> str:
    if ctx.triggered_id == "plain-fast":
        await edge_sleep(0.1)
        value = "fresh-fast"
    else:
        await edge_sleep(2.0)
        value = "stale-slow"
    set_props("edge-plain-side", {"children": value})
    return value
