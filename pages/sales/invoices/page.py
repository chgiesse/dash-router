import dash_mantine_components as dmc

from router import RouteConfig
from router.components import SlotContainer

config = RouteConfig()


async def layout(invoice=SlotContainer, overview=SlotContainer, **kwargs):
    return dmc.SimpleGrid(
        cols=2, children=[dmc.Stack([dmc.Title("Invoices"), overview]), invoice]
    )
