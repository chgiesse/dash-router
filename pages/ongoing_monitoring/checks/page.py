import dash_mantine_components as dmc

from router import RouteConfig

config = RouteConfig(path_template="<cid>", is_static=True)


async def layout(cid: str, **kwargs):
    return dmc.Title(f"OM {cid}")

