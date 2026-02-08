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
            html.P(f"Activity feed for ticket {ticket_id}"),
            html.P("Summary: 3 events"),
            children,
        ],
        style={"display": "flex", "flexDirection": "column", "gap": "4px"},
    )
    return create_box(
        "tests/pages/tickets/[ticket_id]/(activity)/page.py",
        content,
        **kwargs,
    )
