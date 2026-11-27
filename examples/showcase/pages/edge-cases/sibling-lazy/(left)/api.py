from edge_helpers import edge_sleep


async def endpoint(**_):
    await edge_sleep(3.0)
    return "left data"
