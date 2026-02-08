from dash import html
from flash_router import SlotContainer

from components import create_box


async def layout(
    activity: SlotContainer = None,
    detail: SlotContainer = None,
    ticket_id: str | int | None = None,
    **kwargs,
):
    detail_panel = detail or html.Div(
        "No detail loaded.",
        style={"color": "#555"},
    )
    activity_panel = activity or html.Div(
        "No activity loaded.",
        style={"color": "#555"},
    )

    content = html.Div(
        [
            html.H4(f"Ticket {ticket_id}"),
            html.Div(
                [
                    html.Div(
                        [html.H5("Detail"), detail_panel],
                        style={"marginBottom": "12px"},
                    ),
                    html.Div([html.H5("Activity"), activity_panel]),
                ],
                style={
                    "display": "flex",
                    "flexDirection": "column",
                    "gap": "8px",
                },
            ),
        ]
    )

    return create_box(
        "tests/pages/tickets/[ticket_id]/page.py",
        content,
        **kwargs,
    )
