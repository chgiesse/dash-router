from dash import html

from components import create_box


async def layout(ticket_id: str | int | None = None, **kwargs):
    content = html.Div(
        [
            html.P(f"Comments for ticket {ticket_id}"),
            html.Ul(
                [
                    html.Li("Customer: Issue persists after restart."),
                    html.Li("Agent: Investigating log output."),
                ],
                style={"margin": "0"},
            ),
        ],
        style={"display": "flex", "flexDirection": "column", "gap": "4px"},
    )
    return create_box(
        "tests/pages/tickets/[ticket_id]/(activity)/comments/page.py",
        content,
        **kwargs,
    )
