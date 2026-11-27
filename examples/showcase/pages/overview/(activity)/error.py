"""Error boundary of the `(activity)` slot: replaces only this slot when its api/layout raises."""

import dash_mantine_components as dmc

from ui import link, rendered_badge


def error(error: Exception, **_):
    return dmc.Alert(
        dmc.Stack(
            [
                dmc.Text(f"{type(error).__name__}: {error}", size="sm"),
                dmc.Text(
                    "This is (activity)/error.py. KPIs, Revenue and the live feed rendered normally — "
                    "a failing slot never takes the page down.",
                    size="sm",
                    c="dimmed",
                ),
                dmc.Group([link("Recover", "/overview", size="sm"), rendered_badge()], justify="space-between"),
            ],
            gap="xs",
        ),
        title="Recent activity is unavailable",
        color="red",
        variant="light",
    )
