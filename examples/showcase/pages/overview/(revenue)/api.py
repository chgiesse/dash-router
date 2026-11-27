from data import revenue_series, simulate_latency

from ..models import Range


async def endpoint(range: Range = Range.D30, **_):
    # Typed query param: `?range=7d` arrives as `Range.D7`. Only this slot subscribes to it.
    await simulate_latency(2.5)
    return revenue_series(range.days)
