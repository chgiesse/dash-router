from flash_router import ChildContainer
from dash import html

from components import create_box


async def layout(children: ChildContainer = None, **kwargs):
    content = html.Div(
        [
            html.H4("Choose a team", style={"marginBottom": "4px"}),
            html.P(
                "This is the default view for /projects before a team is selected.",
                style={"marginTop": "0"},
            ),
            html.Div(children) if children else None,
        ]
    )
    return create_box(
        "tests/pages/projects/[team_id]/default.py",
        content,
        **kwargs,
    )
