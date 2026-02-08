from flash_router import ChildContainer, RouteConfig
from dash import html

from components import create_box

config = RouteConfig(default_child="overview")


async def layout(children: ChildContainer = None, **kwargs):
    content = html.Div(children)
    return create_box(
        "tests/pages/sales/page.py",
        content,
        **kwargs,
    )
