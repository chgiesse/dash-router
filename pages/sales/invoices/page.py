from router import RouteConfig
import dash_mantine_components as dmc

config = RouteConfig()

async def layout(invoice = None, **kwargs):
    return dmc.SimpleGrid(
        cols=2,
        children=[
            dmc.Stack([
                dmc.Title('Invoices'),
                dmc.Anchor(href='/sales/invoices/1', children='invoice id: 1'),
                dmc.Anchor(href='/sales/invoices/2', children='invoice id: 2'),
                dmc.Anchor(href='/sales/invoices/3', children='invoice id: 3'),
            ]),
            invoice
        ]
    )