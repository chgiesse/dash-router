from data import CUSTOMERS, simulate_latency


async def endpoint(customer_id: int, **_):
    # Runs in parallel with the main branch's api.py for the same URL.
    await simulate_latency(2.8)
    return CUSTOMERS[customer_id]
