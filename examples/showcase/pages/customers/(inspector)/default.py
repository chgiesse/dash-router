"""Rendered when the URL has no match inside `(inspector)` (e.g. /customers/segments)."""

import dash_mantine_components as dmc

from ui import feature_tags, rendered_badge


def default(**_):
    return dmc.Card(
        [
            dmc.Group([dmc.Text("Inspector", fw=600), feature_tags("(inspector)/default.py")], justify="space-between", mb="xs"),
            dmc.Text("Nothing to inspect on this page — this is the slot's default.py.", size="sm", c="dimmed"),
            dmc.Group([rendered_badge()], justify="flex-end", mt="xs"),
        ],
        withBorder=True,
    )
