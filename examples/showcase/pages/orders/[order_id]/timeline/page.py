import dash_mantine_components as dmc

from ui import rendered_badge


def page(data: list[tuple[str, str]], **_):
    return dmc.Stack(
        [
            dmc.Timeline(
                [dmc.TimelineItem(dmc.Text(when, size="xs", c="dimmed"), title=what) for what, when in data],
                active=len(data) - 1,
                bulletSize=18,
            ),
            dmc.Group(
                [dmc.Text("timeline/api.py ≈ 2.5 s behind its own loading.py", size="xs", c="dimmed"), rendered_badge()],
                justify="space-between",
            ),
        ]
    )
