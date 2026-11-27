import dash_mantine_components as dmc

from ui import loading_badge

_TIMELINE_WIDTHS = (108, 124, 84, 152)

loading = dmc.Stack(
    [
        dmc.Timeline(
            [
                dmc.TimelineItem(
                    dmc.Skeleton(height=11, width=78, mt=4, radius="sm"),
                    title=dmc.Skeleton(height=14, width=width, radius="sm"),
                )
                for width in _TIMELINE_WIDTHS
            ],
            active=-1,
            bulletSize=18,
        ),
        dmc.Group(
            [
                dmc.Text("timeline/api.py ≈ 2.5 s behind its own loading.py", size="xs", c="dimmed"),
                loading_badge("timeline/loading.py"),
            ],
            justify="space-between",
        ),
    ]
)
