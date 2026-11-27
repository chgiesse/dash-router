from edge_helpers import edge_sleep


async def endpoint(**_):
    await edge_sleep(1.5)
    return "inner loaded"
