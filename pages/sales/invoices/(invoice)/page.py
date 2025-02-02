from dash import html

from router import RouteConfig

config = RouteConfig(path_template="<invoice_id>")


async def layout(invoice_id=None, **kwargs):
    if invoice_id:
        return html.Div(str(invoice_id))

    return html.Div("Select an invoice")

