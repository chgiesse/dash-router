from data import CUSTOMERS, ORDERS, simulate_latency


async def endpoint(order_id: int, **_):
    # `[order_id]` is coerced to `int` from the URL segment.
    await simulate_latency(2.0)
    order = ORDERS.get(order_id)
    if order is None:
        raise LookupError(f"Order #{order_id} does not exist")
    return {"order": order, "customer": CUSTOMERS[order.customer_id]}
