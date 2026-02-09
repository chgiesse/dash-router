from dash import html
from flash_router import ChildContainer

from components import create_box
from .components import button, url


async def layout(children: ChildContainer = None, **kwargs):
    content = html.Div([children, button, url])
    return create_box(
        "tests/pages/page.py",
        content,
        **kwargs,
    )
