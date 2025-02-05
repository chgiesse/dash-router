import dash_mantine_components as dmc

from router import RouteConfig
from router.components import ChildContainer

from ._components.tabs import SalesTabs

config = RouteConfig(default_child="overview")


async def layout(children: ChildContainer = None, **kwargs):
    tab = children.props.active
    print("TAB: ", tab, flush=True)
    return dmc.Stack(
        m=0,
        p=0,
        children=[dmc.Title("Sales"), SalesTabs(tab), dmc.Divider(), children],
    )
