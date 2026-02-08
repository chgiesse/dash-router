from dash import html

from components import create_box


async def layout(ticket_id: str | int | None = None, **kwargs):
    content = html.Div(
        [
            html.P(f"Summary for ticket {ticket_id}"),
            html.Ul(
                [
                    html.Li("Priority: High"),
                    html.Li("Status: Open"),
                ],
                style={"margin": "0"},
            ),
        ],
        style={"display": "flex", "flexDirection": "column", "gap": "4px"},
    )
    return create_box(
        "tests/pages/tickets/[ticket_id]/(detail)/summary/page.py",
        content,
        **kwargs,
    )
