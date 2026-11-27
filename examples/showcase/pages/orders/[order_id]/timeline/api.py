from data import ORDERS, order_timeline, simulate_latency


async def endpoint(order_id: int, **_):
    await simulate_latency(2.5)
    return order_timeline(ORDERS[order_id])
