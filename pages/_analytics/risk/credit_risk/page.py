from router import RouteConfig
import dash_mantine_components as dmc 


config = RouteConfig()


async def layout(**kwargs):
    return dmc.Title('Credit Risk')