from router import RouteConfig
import dash_mantine_components as dmc

config = RouteConfig(
    view_template='[invoice]'
)

async def layout(invoice = None, **kwargs):
    return dmc.SimpleGrid(
        cols=2,
        children=[
            dmc.Title('Invoices'),
            dmc.Text(invoice or 'This is the invoice section')
        ]
    )