"""Notes: a plain route with no `api.py` and no `loading.py`.

Every visit renders the layout again, so the "rendered" badge changes each time.
"""

import dash_mantine_components as dmc

from data import ORDERS
from ui import rendered_badge


def page(order_id: int, **_):
    order = ORDERS[order_id]
    return dmc.Stack(
        [
            dmc.Blockquote(
                f"Customer asked to bundle order #{order.id} with their next shipment. "
                "Fragile items — double box.",
                cite="— Support, internal note",
            ),
            dmc.Textarea(placeholder="Add a note (kept while you stay on the page)…", autosize=True, minRows=2),
            dmc.Group(
                [
                    dmc.Text("notes/page.py · no api.py / loading.py · the badge changes on every visit", size="xs", c="dimmed"),
                    rendered_badge(),
                ],
                justify="space-between",
            ),
        ]
    )
