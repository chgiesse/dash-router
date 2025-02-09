import dash_mantine_components as dmc

from .._components.cards import card
from .._components.figures import create_water_chart


async def layout(**kwargs):
    # def layout(**kwargs):
    return dmc.Stack(
        [
            dmc.Title(f"All items for invoice id: {kwargs.get('invoice_id')}", order=3),
            create_water_chart(),
            dmc.Group([card, card], grow=True, className="fade-in-right"),
        ]
    )
