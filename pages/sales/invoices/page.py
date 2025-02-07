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
                    dmc.SemiCircleProgress(
                        value=76,
                        size=300,
                        thickness=20,
                        transitionDuration=250,
                        label="paid invoices",
                        mx="auto",
                        labelPosition="center",
                    ),
                    bar_chart,
                    overview,
                ],
                gap="lg",
            ),
            invoice,
        ],
    )
