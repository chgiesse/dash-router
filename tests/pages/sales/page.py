from flash_router import ChildContainer, RouteConfig
from dash import dcc, html

from components import create_box

config = RouteConfig(default_child="overview")


async def layout(children: ChildContainer = None, **kwargs):
    sample_links = html.Ul(
        [
            html.Li(dcc.Link("/sales", href="/sales")),
            html.Li(dcc.Link("/sales/overview", href="/sales/overview")),
            html.Li(dcc.Link("/sales/dashboard", href="/sales/dashboard")),
            html.Li(dcc.Link("/sales/analytics", href="/sales/analytics")),
            html.Li(dcc.Link("/sales/invoices/1001", href="/sales/invoices/1001")),
        ],
        style={"margin": "0"},
    )

    detail_panel = children or html.Div(
        "Select a sales view to continue.",
        style={"color": "#555"},
    )

    content = html.Div(
        [
            html.Div(
                [
                    html.H3("Sales"),
                    html.P(
                        "Explore dashboards and invoices under /sales.",
                        style={"marginTop": "0"},
                    ),
                    html.P("Try these URLs:", style={"marginBottom": "4px"}),
                    sample_links,
                ],
                style={"flex": "1"},
            ),
            html.Div(
                [html.H4("Sales Workspace"), detail_panel],
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
        "tests/pages/sales/page.py",
        content,
        **kwargs,
    )
