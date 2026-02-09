from dash import html
from flash_router import SlotContainer

from components import create_box


async def layout(
    summary: SlotContainer = None,
    ticket_id: str | int | None = None,
    **kwargs,
):
    summary_panel = summary or html.Div(
        "No summary loaded.",
        style={"color": "#555"},
    )
    content = html.Div(
        [
            html.P(f"Detail panel for ticket {ticket_id}"),
            summary_panel,
        ],
        style={"display": "flex", "flexDirection": "column", "gap": "6px"},
    )
    return create_box(
        "tests/pages/tickets/[ticket_id]/(detail)/page.py",
        content,
        **kwargs,
    )
