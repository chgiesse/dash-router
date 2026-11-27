from data import ORDERS, OrderStatus, simulate_latency


async def endpoint(**_):
    await simulate_latency(1.5)
    orders = list(ORDERS.values())
    return {
        "orders": len(orders),
        "open": sum(o.status is OrderStatus.OPEN for o in orders),
        "delayed": sum(o.status is OrderStatus.DELAYED for o in orders),
        "revenue": sum(o.total for o in orders),
    }
