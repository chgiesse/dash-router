from flash_router import SlotContainer
from dash import html

from components import create_box


async def layout(figures: SlotContainer = None, **kwargs):
    content = html.Div(figures)
    return create_box(
        "tests/pages/sales/analytics/page.py",
        content,
        **kwargs,
    )
