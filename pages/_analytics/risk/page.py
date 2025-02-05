import dash_mantine_components as dmc

from router import RouteConfig

config = RouteConfig()


async def layout(**kwargs):
    return dmc.Title("RV Risk")

