import dash_mantine_components as dmc
from dash import html

from dash_router import ChildContainer
from ui import feature_tags


def page(children: ChildContainer, **_):
    # Always render `children`: when the URL later matches `accounts/[customer_id]`, the router
    # patches this container in place without re-rendering the slot wrapper.
    hint = dmc.Text("Open a customer to inspect their risk profile.", size="sm", c="dimmed", className="slot-hint")
    return dmc.Card(
        [
            dmc.Group([dmc.Text("Inspector", fw=600), feature_tags("(inspector) slot route")], justify="space-between", mb="xs"),
            html.Div([children, hint], className="slot-children"),
        ],
        withBorder=True,
        mih=195,
    )
