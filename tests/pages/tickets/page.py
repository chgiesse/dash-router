from dash import dcc, html
from flash_router import ChildContainer

from components import create_box


async def layout(children: ChildContainer = None, **kwargs):
    sample_links = html.Ul(
        [
            html.Li(dcc.Link("/tickets", href="/tickets")),
            html.Li(dcc.Link("/tickets/1001", href="/tickets/1001")),
        ],
        style={"margin": "0"},
    )

    detail_panel = children or html.Div(
        "Select a ticket to see details.",
        style={"color": "#555"},
    )

    content = html.Div(
        [
            html.Div(
                [
                    html.H3("Support Tickets"),
                    html.P(
                        "Ticket selection lives under /tickets/<ticket_id>.",
                        style={"marginTop": "0"},
                    ),
                    html.P("Try these URLs:", style={"marginBottom": "4px"}),
                    sample_links,
                ],
                style={"flex": "1"},
            ),
            html.Div(
                [html.H4("Ticket Workspace"), detail_panel],
                style={
                    "flex": "1",
                    "borderLeft": "1px solid #ddd",
                    "paddingLeft": "12px",
                },
            ),
        ],
        style={"display": "flex", "gap": "16px"},
    )

    return create_box(
        "tests/pages/tickets/page.py",
        content,
        **kwargs,
    )
