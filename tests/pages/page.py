from dash import html
from flash_router import ChildContainer
from flash_router.components import RootContainer
from flash import set_props

from components import create_box
from .components import button, url, second_button, loader


async def layout(children: ChildContainer = None, **kwargs):
    content = html.Div([children, button, second_button, loader])
    return create_box(
        "tests/pages/page.py",
        content,
        **kwargs,
    )
