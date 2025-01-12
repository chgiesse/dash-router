from router import RouteConfig
import dash_mantine_components as dmc 


config = RouteConfig(has_slots=True)


async def layout(**kwargs):
    return dmc.Title('RV Risk')