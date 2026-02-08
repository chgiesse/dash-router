from flash_router import ChildContainer, SlotContainer
from dash import html

from components import create_box


async def layout(
    children: ChildContainer = None,
    slot_1: SlotContainer = None,
    slot_2: SlotContainer = None,
    **kwargs,
):
    content = html.Div(
        [
            html.Div(
                [slot_1, slot_2], style={"display": "flex", "flexDirection": "column"}
            ),
            children,
        ]
    )
    return create_box(
        "tests/pages/nested_route/page.py",
        content,
        **kwargs,
    )
