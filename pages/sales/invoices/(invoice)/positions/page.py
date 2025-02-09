import dash_mantine_components as dmc

from .._components.figures import donut_chart


async def layout(**kwargs):
    # def layout(**kwargs):
    return dmc.Stack(
        [
            dmc.Title(
                f"All positions for invoice id: {kwargs.get('invoice_id')}", order=3
            ),
            donut_chart,
        ]
    )
