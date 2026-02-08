from flash_router import SlotContainer
from dash import html

from components import create_box


async def layout(
    ranks: SlotContainer = None,
    revenue: SlotContainer = None,
    sentiment: SlotContainer = None,
    **kwargs,
):
    content = html.Div(
        [ranks, revenue, sentiment],
        style={"display": "flex", "gap": "8px", "flexWrap": "wrap"},
    )
    return create_box(
        "tests/pages/sales/dashboard/page.py",
        content,
        **kwargs,
    )
