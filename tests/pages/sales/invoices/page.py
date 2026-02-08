from flash_router import ChildContainer, SlotContainer
from dash import html

from components import create_box


async def layout(
    children: ChildContainer = None,
    overview: SlotContainer = None,
    **kwargs,
):
    content = html.Div(
        [overview, children],
        style={"display": "flex", "flexDirection": "column", "gap": "8px"},
    )
    return create_box(
        "tests/pages/sales/invoices/page.py",
        content,
        **kwargs,
    )
