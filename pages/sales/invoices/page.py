from router import RouteConfig
import dash_mantine_components as dmc

config = RouteConfig()

async def layout(invoice = None, overview = None, **kwargs):
    return dmc.SimpleGrid(
        cols=2,
        children=[
            dmc.Stack([
                dmc.Title('Invoices'),
                overview
            ]),
            invoice
        ]
    )