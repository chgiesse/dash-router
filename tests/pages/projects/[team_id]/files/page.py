from flash_router import ChildContainer
from dash import html

from components import create_box


async def layout(
    children: ChildContainer = None,
    team_id: str | None = None,
    **kwargs,
):
    content = html.Div(children)
    return create_box(
        "tests/pages/projects/[team_id]/files/page.py",
        content,
        team_id=team_id,
        **kwargs,
    )
