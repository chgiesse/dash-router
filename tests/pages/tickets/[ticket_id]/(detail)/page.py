from dash import html
from flash_router import ChildContainer

from components import create_box


async def layout(
    children: ChildContainer = None,
    ticket_id: str | int | None = None,
    **kwargs,
):
    content = html.Div(
        [
            html.P(f"Detail panel for ticket {ticket_id}"),
            children,
        ],
        style={"display": "flex", "flexDirection": "column", "gap": "6px"},
    )
    return create_box(
        "tests/pages/tickets/[ticket_id]/(detail)/page.py",
        content,
        **kwargs,
    )
