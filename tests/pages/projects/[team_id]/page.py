from typing import Any
from flash_router.components import ChildContainer
from flash_router.core.routing import RouteConfig
from dash import html, dcc


config = RouteConfig(
    default=html.Div(
        [
            html.H4("Choose a team", className="m-0"),
            html.P("This is the default view for /projects before a team is selected.", className="muted"),
        ]
    )
)


async def layout(
    children: ChildContainer,
    team_id: str,
    **_: Any,
):
    # Team header and breadcrumb
    header = html.Div(
        [
            html.Div([html.H3(team_id or "(unknown)", className="m-0"), html.Div(f"/projects/{team_id}", className="breadcrumb")]),
            dcc.Link("Files", href=f"/projects/{team_id}/files", className="btn"),
        ],
        className="header",
    )

    content = html.Div([header, html.Div(children)])
    return content
