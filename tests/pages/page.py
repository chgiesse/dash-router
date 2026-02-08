from flash_router import ChildContainer
from dash import html

from components import create_box


async def layout(children: ChildContainer = None, **kwargs):
    content = html.Div(children)
    return create_box(
        "tests/pages/page.py",
        content,
        **kwargs,
    )
