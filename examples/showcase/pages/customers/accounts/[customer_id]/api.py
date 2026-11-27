from data import CUSTOMERS, ORDERS, simulate_latency


async def endpoint(customer_id: int, **_):
    await simulate_latency(1.8)
    customer = CUSTOMERS.get(customer_id)
    if customer is None:
        raise LookupError(f"Customer {customer_id} does not exist")
    orders = sorted((o for o in ORDERS.values() if o.customer_id == customer_id), key=lambda o: o.placed, reverse=True)
    return {"customer": customer, "orders": orders}
