"""Skeleton of `summary/page.py` while `summary/api.py` runs."""

import dash_mantine_components as dmc

from ui import feature_tags, loading_badge

_FACT_SKELETONS = (
    ("Status", 72),
    ("Placed", 92),
    ("Items", 36),
    ("Total", 82),
    ("Customer segment", 88),
)

_SUMMARY_SKELETON = dmc.Stack(
    [
        dmc.SimpleGrid(
            [
                dmc.Paper(
                    [
                        dmc.Text(label, size="xs", c="dimmed"),
                        dmc.Skeleton(height=18, width=width, mt=6, radius="sm"),
                    ],
                    withBorder=True,
                    p="sm",
                )
                for label, width in _FACT_SKELETONS
            ],
            cols={"base": 2, "md": 3},
        ),
        dmc.Group(
            [
                dmc.Skeleton(height=12, width=235, radius="sm"),
                dmc.Skeleton(height=18, width=90, radius="sm"),
            ],
            justify="space-between",
        ),
    ]
)

loading = dmc.Stack(
    [
        _SUMMARY_SKELETON,
        dmc.Group(
            [
                feature_tags("summary/api.py ≈ 2.0 s", "summary/loading.py"),
                loading_badge(),
            ],
            justify="space-between",
        ),
    ],
    gap="md",
    mih=290,
)
