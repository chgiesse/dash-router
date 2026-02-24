from flash_router import ChildContainer, RouteConfig
from dash import html, dcc

from components import create_box

config = RouteConfig(
    default=html.Div(
        [
            html.H4("Choose a team", className="m-0"),
            html.P("This is the default view for /projects before a team is selected.", className="muted"),
        ]
    )
)


async def layout(
    children: ChildContainer = None,
    team_id: str | None = None,
    **kwargs,
):
    # Team header and breadcrumb
    header = html.Div(
        [
            html.Div([html.H3(team_id or "(unknown)", className="m-0"), html.Div(f"/projects/{team_id}", className="breadcrumb")]),
            dcc.Link("Files", href=f"/projects/{team_id}/files", className="btn"),
        ],
        className="header",
    )

    content = html.Div([header, html.Div(children or [])])
    return create_box(
        "tests/pages/projects/[team_id]/page.py",
        content,
        team_id=team_id,
        **kwargs,
    )
