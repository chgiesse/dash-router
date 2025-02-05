import dash_mantine_components as dmc

from router import RouteConfig
from router.components import ChildContainer

from ._components.tabs import SalesTabs

config = RouteConfig(view_template="[sales_sub_view]", default_child="overview")


async def layout(sales_sub_view: ChildContainer = None, **kwargs):
    tab = sales_sub_view.props.active
    print("TAB: ", tab, flush=True)
    return dmc.Stack(
        m=0,
        p=0,
        children=[dmc.Title("Sales"), SalesTabs(tab), dmc.Divider(), sales_sub_view],
    )
