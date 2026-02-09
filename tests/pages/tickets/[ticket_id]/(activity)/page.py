from dash import html
from flash_router import SlotContainer

from components import create_box


async def layout(
    comments: SlotContainer = None,
    ticket_id: str | int | None = None,
    **kwargs,
):
    comments_panel = comments or html.Div(
        "No comments loaded.",
        style={"color": "#555"},
    )
    content = html.Div(
        [
            html.P(f"Activity feed for ticket {ticket_id}"),
            html.P("Summary: 3 events"),
            comments_panel,
        ],
        style={"display": "flex", "flexDirection": "column", "gap": "4px"},
    )
    return create_box(
        "tests/pages/tickets/[ticket_id]/(activity)/page.py",
        content,
        **kwargs,
    )
