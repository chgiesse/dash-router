import dash_mantine_components as dmc

from router import RouteConfig

config = RouteConfig(is_static=True)


async def layout(**kwargs):
    return dmc.Title("OM History")

