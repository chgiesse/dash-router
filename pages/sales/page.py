from ._components.tabs import SalesTabs 
from router import RouteConfig

import dash_mantine_components as dmc 


config = RouteConfig(
    view_template='[sales_sub_view]'
)


async def layout(sales_sub_view = None, **kwargs):
    print('sales_sub_view', sales_sub_view, flush=True)
    tab = kwargs.get('child_segment', 'overview')
    return dmc.Stack(
        m=0,
        p=0,
        children=[
            dmc.Title('Sales'),
            SalesTabs(tab),
            dmc.Divider(),
            sales_sub_view
        ]
    )


