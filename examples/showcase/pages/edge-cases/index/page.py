"""Index of the edge cases: what each route does and what you should see."""

import dash_mantine_components as dmc

from edge_helpers import CASES, edge_badge, record_render
from ui import link

URL = "/edge-cases"


def page(**_):
    cards = [
        dmc.Card(
            [
                dmc.Text(case.title, fw=600),
                dmc.Text(case.href, size="xs", c="dimmed", ff="monospace"),
                dmc.Text(f"Expected: {case.expected}", size="sm"),
                link("Open this case", case.href, size="sm"),
            ],
            withBorder=True,
            radius="md",
            padding="md",
        )
        for case in CASES
    ]
    return dmc.Stack(
        [
            dmc.Group(
                [
                    dmc.Text(
                        "Every case is deterministic: api.py and generator delays are fixed, scaled only by EDGE_DELAY_SCALE. "
                        "No query parameter controls delays. Compare the render counters and pids in the badges.",
                        size="sm",
                        c="dimmed",
                    ),
                    edge_badge("index", URL, count=record_render("index", URL)),
                ],
                justify="space-between",
                align="flex-start",
            ),
            dmc.SimpleGrid(cards, cols={"base": 1, "md": 2}),
        ],
        gap="md",
    )
