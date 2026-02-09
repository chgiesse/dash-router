from flash_router import ChildContainer, RouteConfig
from dash import html

from components import create_box

config = RouteConfig(
    default_child="items", default=html.Div("Default State if no invoice selected")
)


async def layout(
    children: ChildContainer = None,
    invoice_id: str | int | None = None,
    **kwargs,
):
    content = html.Div(children)
    return create_box(
        "tests/pages/sales/invoices/[invoice_id]/page.py",
        content,
        **kwargs,
    )
