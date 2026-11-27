from data import CUSTOMERS, ORDERS, simulate_latency


class UpstreamError(RuntimeError):
    pass


async def endpoint(fail: str | None = None, **_):
    await simulate_latency(3.5)
    if fail == "activity":
        raise UpstreamError("activity service timed out after 3.5 s")
    recent = sorted(ORDERS.values(), key=lambda o: (o.placed, o.id), reverse=True)[:6]
    return [
        {"order": o.id, "customer": CUSTOMERS[o.customer_id].name, "status": o.status.value, "placed": o.placed.isoformat()}
        for o in recent
    ]
