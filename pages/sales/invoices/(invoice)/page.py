from router import RouteConfig
from dash import html

config = RouteConfig(
    path_template='<invoice_id>'
)

async def layout(invoice_id = None, **kwargs):
    return html.Div(str(invoice_id))
    