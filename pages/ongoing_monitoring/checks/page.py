from router import RouteConfig
import dash_mantine_components as dmc 


config = RouteConfig(path_template='<cid>')


async def layout(cid: str, **kwargs):
    return dmc.Title(f'OM {cid}')