from flash_router import ChildContainer
from dash import dcc, html

from components import create_box


async def layout(children: ChildContainer = None, **kwargs):
    sample_links = html.Ul(
        [
            html.Li(dcc.Link("home", href="/")),
            html.Li(dcc.Link("/projects", href="/projects")),
            html.Li(dcc.Link("/projects/alpha", href="/projects/alpha")),
            html.Li(dcc.Link("/projects/alpha/files", href="/projects/alpha/files")),
            html.Li(
                dcc.Link(
                    "/projects/alpha/files/design/spec.md",
                    href="/projects/alpha/files/design/spec.md",
                )
            ),
        ],
        style={"margin": "0"},
    )

    detail_panel = children or html.Div(
        "Select a project to see details.",
        style={"color": "#555"},
    )

    content = html.Div(
        [
            html.Div(
                [
                    html.H3("Projects"),
                    html.P(
                        "Team projects live under /projects/<team_id>.",
                        style={"marginTop": "0"},
                    ),
                    html.P("Try these URLs:", style={"marginBottom": "4px"}),
                    sample_links,
                ],
                style={"flex": "1"},
            ),
            html.Div(
                [html.H4("Project Workspace"), detail_panel],
                style={
                    "flex": "1",
                    "borderLeft": "1px solid #ddd",
                    "paddingLeft": "12px",
                    "width": "50%",
                },
            ),
        ],
        style={"display": "flex", "gap": "16px"},
    )
    return create_box(
        "tests/pages/projects/page.py",
        content,
        **kwargs,
    )
