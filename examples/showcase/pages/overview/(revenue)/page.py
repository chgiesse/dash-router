import asyncio
import random
from contextlib import suppress
from datetime import timedelta
from itertools import count

import dash_mantine_components as dmc
from dash import Patch, set_props
from dash.exceptions import MissingCallbackContextException

from data import TODAY
from ui import feature_tags, rendered_badge

from ..models import Range


class RevenueChart(dmc.Stack):
    class ids:
        chart = "revenue-area-chart"
        status = "revenue-chart-status"

    def __init__(self, series: list[dict[str, object]]) -> None:
        super().__init__(
            [
                dmc.Group(
                    [
                        dmc.Group(
                            [
                                feature_tags("(revenue)/api.py ≈ 2.5 s", "typed query param `range`", "Patch every 1 s"),
                                dmc.Text("live · 1 s", id=self.ids.status, size="xs", c="dimmed"),
                            ],
                            gap="xs",
                        ),
                        rendered_badge(),
                    ],
                    justify="space-between",
                ),
                dmc.AreaChart(
                    id=self.ids.chart,
                    h=240,
                    data=series,
                    dataKey="date",
                    series=[
                        {"name": "Revenue", "color": "indigo.6"},
                        {"name": "Refunds", "color": "red.5"},
                    ],
                    curveType="monotone",
                    withDots=False,
                    # Draws in on mount; `append_point` turns the animation off once live updates start.
                    areaProps={"isAnimationActive": True, "animationDuration": 1200, "animationEasing": "ease-out"},
                ),
            ],
            gap="sm",
        )

    @classmethod
    def append_point(cls, point: dict[str, object], step: int) -> None:
        patch = Patch()
        del patch[0]
        patch.append(point)
        chart_props: dict[str, object] = {"data": patch}
        if step == 1:
            chart_props["areaProps"] = {"isAnimationActive": False}
        with suppress(MissingCallbackContextException):
            set_props(cls.ids.chart, chart_props)
            set_props(cls.ids.status, {"children": f"live · {step}s"})


async def page(data: list[dict[str, object]], range: Range = Range.D30, **_):
    yield RevenueChart(data)

    rng = random.Random(range.days + 100)
    for step in count(1):
        # Let the initial draw-in animation finish before the first live point disables animation.
        await asyncio.sleep(2.5 if step == 1 else 1.0)
        day = TODAY + timedelta(days=step)
        point: dict[str, object] = {
            "date": day.strftime("%b %d"),
            "Revenue": rng.randint(8_000, 26_000),
            "Refunds": rng.randint(200, 3_000),
        }
        yield RevenueChart.append_point(point, step)
