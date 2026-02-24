from flash_router import ChildContainer
from dash import dcc, html

from components import create_box


async def layout(children: ChildContainer = None, **kwargs):
    # Sidebar: list of teams
    teams = html.Div(
        [
            html.H3("Teams"),
            html.Div(
                [
                    dcc.Link(
                        html.Div([html.Div("A", className="team-icon"), html.Div("Alpha")], className="team-link"),
                        href="/projects/alpha",
                        className="team-link",
                    ),
                    dcc.Link(
                        html.Div([html.Div("B", className="team-icon"), html.Div("Beta")], className="team-link"),
                        href="/projects/beta",
                        className="team-link",
                    ),
                    dcc.Link(
                        html.Div([html.Div("C", className="team-icon"), html.Div("Client")], className="team-link"),
                        href="/projects/client",
                        className="team-link",
                    ),
                ],
                className="teams",
            ),
        ],
        className="sidebar",
    )

    # Main area: header + file grid (or children)
    detail_panel = children or html.Div(
        [
            html.Div("Select a team or open a folder to explore files.", className="muted"),
        ]
    )

    header = html.Div(
        [
            html.Div([html.H2("Projects", className="title"), html.Div("/projects", className="breadcrumb")]),
            html.Div([html.Button("New", className="btn"), html.Button("Upload", className="btn primary")], className="file-toolbar"),
        ],
        className="header",
    )

    # Example quick links / sample files to demonstrate navigation
    quick_files = html.Div(
        [
            html.Div("Quick Links", className="muted"),
            html.Div(
                [
                    dcc.Link("/projects/alpha/files", href="/projects/alpha/files", className="btn"),
                    " ",
                    dcc.Link("/projects/alpha/files/design", href="/projects/alpha/files/design", className="btn"),
                    " ",
                    dcc.Link("/projects/alpha/files/photos", href="/projects/alpha/files/photos", className="btn"),
                ],
                style={"marginTop": "8px"},
            ),
        ],
    )

    main = html.Div([header, quick_files, detail_panel], className="main")

    content = html.Div([teams, main], className="explorer")

    return create_box("tests/pages/projects/page.py", content, **kwargs)
