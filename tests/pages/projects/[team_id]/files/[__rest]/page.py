from dash import html

from components import create_box


async def layout(
    rest: list | None = None,
    team_id: str | None = None,
    **kwargs,
):
    return create_box(
        "tests/pages/projects/[team_id]/files/[__rest]/page.py",
        html.Div("catch-all"),
        rest=rest or [],
        team_id=team_id,
        **kwargs,
    )
