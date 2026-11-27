import dash_mantine_components as dmc

from ui import rendered_badge


def page(**_):
    return dmc.Group(
        [dmc.Text("Segments clear the pin ((pinned)/segments/page.py).", size="sm", c="dimmed"), rendered_badge()],
        justify="space-between",
    )
