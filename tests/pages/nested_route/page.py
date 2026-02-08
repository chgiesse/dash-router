from flash_router import ChildContainer, SlotContainer
from dash import dcc, html

from components import create_box


async def layout(
    children: ChildContainer = None,
    slot_1: SlotContainer = None,
    slot_2: SlotContainer = None,
    **kwargs,
):
    sample_links = html.Ul(
        [
            html.Li(dcc.Link("/nested_route", href="/nested_route")),
            html.Li(dcc.Link("/nested_route/child_1", href="/nested_route/child_1")),
            html.Li(dcc.Link("/nested_route/child_2", href="/nested_route/child_2")),
            html.Li(dcc.Link("/nested_route/child_3", href="/nested_route/child_3")),
        ],
        style={"margin": "0"},
    )

    detail_panel = html.Div(
        [
            html.Div(
                [slot_1, slot_2],
                style={"display": "flex", "flexDirection": "column"},
            ),
            children or html.Div(
                "Choose a nested route to continue.",
                style={"color": "#555"},
            ),
        ]
    )

    content = html.Div(
        [
            html.Div(
                [
                    html.H3("Nested Routes"),
                    html.P(
                        "Navigate through nested children and slots.",
                        style={"marginTop": "0"},
                    ),
                    html.P("Try these URLs:", style={"marginBottom": "4px"}),
                    sample_links,
                ],
                style={"flex": "1"},
            ),
            html.Div(
                [html.H4("Nested Workspace"), detail_panel],
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
        "tests/pages/nested_route/page.py",
        content,
        **kwargs,
    )
