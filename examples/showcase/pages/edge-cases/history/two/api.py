from edge_helpers import edge_sleep


async def endpoint(**_):
    await edge_sleep(0.4)
    return "two"
