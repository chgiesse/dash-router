from flash_router import ChildContainer, RouteConfig
from dash import html

from components import create_box

config = RouteConfig(
    default=html.Div(
        [
            html.H4("Choose a team", style={"marginBottom": "4px"}),
            html.P(
                "This is the default view for /projects before a team is selected.",
                style={"marginTop": "0"},
            ),
        ]
    )
)


async def layout(
    children: ChildContainer = None,
    team_id: str | None = None,
    **kwargs,
):
    content = html.Div(children)
    return create_box(
        "tests/pages/projects/[team_id]/page.py",
        content,
        team_id=team_id,
        **kwargs,
    )
