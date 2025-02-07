import dash_mantine_components as dmc
from dash import html

from .._components.figures import create_water_chart


# async def layout(**kwargs):
def layout(**kwargs):
    return dmc.Stack(
        [
            html.Div(f"All items for invoice id: {kwargs.get('invoice_id')}"),
            create_water_chart(),
        ]
    )
