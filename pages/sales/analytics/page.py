from router import RouteConfig
import dash_mantine_components as dmc

config = RouteConfig(
    path_template='<rn>'
)

async def layout(rn = 1):
    return [dmc.Title(f'Sales Analytics {rn}')]

