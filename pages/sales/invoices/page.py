import dash_mantine_components as dmc

from router import RouteConfig
from router.components import SlotContainer

from ._components.figures import bar_chart

config = RouteConfig()


async def layout(invoice=SlotContainer, overview=SlotContainer, **kwargs):
    # def layout(invoice=SlotContainer, overview=SlotContainer, **kwargs):
    return dmc.SimpleGrid(
        cols=2,
        children=[
            dmc.Stack(
                [
                    dmc.Card(dmc.Stack([dmc.Title("Top Vendors", order=2), bar_chart])),
                    dmc.Card(dmc.Stack([dmc.Title("Invoice list", order=3), overview])),
                ],
                gap="lg",
            ),
            dmc.Stack(
                [
                    dmc.Box(invoice, mih=50),
                    dmc.Alert(
                        "This is still the invoices section",
                        title="Invoices section!",
                    ),
                ]
            ),
        ],
    )
