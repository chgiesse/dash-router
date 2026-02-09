from dash import html, dcc

from components import create_box


async def layout(team_id, **kwargs):
    def create_url(part):
        return f"""
            /projects/{team_id}/files/{part}
        """

    content = html.Div(
        [
            html.H4("Default view", style={"marginBottom": "4px"}),
            html.P(
                "This is the default view.",
                style={"marginTop": "0"},
            ),
            html.Div(
                [
                    dcc.Link("Docs", href=create_url("projects")),
                    " | ",
                    dcc.Link("Photos", href=create_url("photos")),
                    " | ",
                    dcc.Link("Videos", href=create_url("videos")),
                    " | ",
                    dcc.Link("Downloads", href=create_url("downloads")),
                ],
                style={"marginTop": "8px"},
            ),
        ]
    )
    return create_box(
        "tests/pages/projects/[team_id]/default.py",
        content,
        **kwargs,
    )
