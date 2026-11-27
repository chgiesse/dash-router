"""Edge cases: races, streams and fallbacks, each one a route you can reproduce by hand.

This layout stays mounted while you move between cases, so the jump nav and the debug panel
(worker pid, active generators, mounted router containers) remain visible during each race.
"""

import dash_mantine_components as dmc

from dash_router import ChildContainer, RouteConfig
from edge_helpers import CASES, debug_panel
from ui import feature_tags

config = RouteConfig(default_child="index", title="Edge cases · Northwind Ops")


def page(children: ChildContainer, **_):
    jump = dmc.Group(
        [dmc.Anchor("Index", href="/edge-cases", size="xs")]
        + [dmc.Anchor(case.label, href=case.href, size="xs") for case in CASES],
        gap="xs",
    )
    return dmc.Stack(
        [
            dmc.Stack(
                [
                    dmc.Title("Edge cases", order=2),
                    feature_tags("superseded navigations", "lazy races", "generators", "error boundaries"),
                ],
                gap=4,
            ),
            debug_panel(),
            jump,
            dmc.Box(children),
        ],
        gap="md",
    )
