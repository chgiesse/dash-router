from edge_helpers import edge_sleep


class UpstreamError(RuntimeError):
    pass


async def endpoint(**_):
    await edge_sleep(0.5)
    raise UpstreamError("api-err: upstream timed out after 0.5 s")
