from flash_router import RouteConfig, SlotContainer
from dash import html

from components import create_box

config = RouteConfig(default_child="child-11")


async def layout(
    slot_31: SlotContainer = None,
    slot_32: SlotContainer = None,
    slot_33: SlotContainer = None,
    slot_34: SlotContainer = None,
    slot_35: SlotContainer = None,
    **kwargs,
):
    content = html.Div(
        [
            html.Div(
                [slot_31, slot_32],
                style={"display": "flex", "gap": "8px"},
            ),
            html.Div(
                [slot_33, slot_34, slot_35],
                style={"display": "flex", "gap": "8px", "flexWrap": "wrap"},
            ),
        ]
    )
    return create_box(
        "tests/pages/nested_route/child_3/page.py",
        content,
        **kwargs,
    )
