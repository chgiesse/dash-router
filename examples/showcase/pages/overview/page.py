"""Overview: four passive `(slots)` rendered side by side.

Each slot has its own `api.py`; the router starts all of them at once, sends the `loading.py`
skeletons in the first frame and streams every slot as soon as its data is ready.

The revenue range control lives here, outside the `(revenue)` lazy boundary, so switching
`7d / 30d / 90d` replaces only the chart with its skeleton while keeping the control mounted.
This layout reads its initial value from `**query` (no `range` parameter), so it does not
subscribe to `range` and never re-renders when the range changes.
"""

import dash_mantine_components as dmc

from dash_router import RouteConfig, SlotContainer
from ui import feature_tags, rendered_badge

from .models import Range

config = RouteConfig(title="Overview · Northwind Ops")


def _initial_range(query: dict) -> Range:
    try:
        return Range(query.get("range", Range.D30.value))
    except ValueError:
        return Range.D30


def _revenue_card(revenue: SlotContainer, initial: Range) -> dmc.Card:
    control = dmc.UrlParam(
        dmc.SegmentedControl(
            id="revenue-range",
            value=initial.value,
            data=[r.value for r in Range],
            size="xs",
        ),
        param="range",
        default=Range.D30.value,
        twoWay=True,
    )
    header = dmc.Group(
        [
            dmc.Stack(
                [
                    dmc.Text("Revenue", fw=600),
                    feature_tags("control in overview/page.py", "dmc.UrlParam (no callback)"),
                ],
                gap=4,
            ),
            control,
        ],
        justify="space-between",
        align="flex-start",
        mb="sm",
    )
    return dmc.Card([header, dmc.Box(revenue, mih=304)], withBorder=True, radius="md", padding="md", h="100%")


def page(
    kpis: SlotContainer,
    revenue: SlotContainer,
    activity: SlotContainer,
    live: SlotContainer,
    **query,
):
    return dmc.Stack(
        [
            dmc.Group(
                [
                    dmc.Stack(
                        [
                            dmc.Title("Operations overview", order=2),
                            feature_tags("4 parallel (slots)", "api.py per slot", "streamed in arrival order"),
                        ],
                        gap=4,
                    ),
                    rendered_badge("page rendered"),
                ],
                justify="space-between",
                align="flex-start",
            ),
            dmc.Box(kpis, mih=112),
            dmc.Grid(
                [
                    dmc.GridCol(_revenue_card(revenue, _initial_range(query)), span={"base": 12, "lg": 8}),
                    dmc.GridCol(dmc.Box(live, h=388), span={"base": 12, "lg": 4}),
                ]
            ),
            dmc.Box(activity, mih=404),
        ],
        gap="md",
    )
