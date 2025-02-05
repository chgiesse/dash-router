import dash_mantine_components as dmc
from dash import html

from router import RouteConfig

config = RouteConfig(path_template="<invoice_id>")


async def layout(invoice_id=None, children=None, **kwargs):
    if not invoice_id:
        return html.Div("Select an invoice")

    return dmc.Stack(
        [
            html.Div("Invoice ID: " + str(invoice_id)),
            dmc.Anchor(
                href=f"/sales/invoices/{str(invoice_id)}/items",
                children="invoice id: 1",
            ),
            dmc.Anchor(
                href=f"/sales/invoices/{str(invoice_id)}/positions",
                children="invoice id: 2",
            ),
            dmc.Divider(),
            html.Div(children),
        ]
    )
