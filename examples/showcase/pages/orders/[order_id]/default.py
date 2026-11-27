"""Orders empty state: `[order_id]/default.py`, rendered at `/orders` when no order is selected.

Because `[order_id]` defines `default.py`, `/orders` matches it in `default` mode without calling
`[order_id]/page.py` or its children. Picking an order switches `[order_id]` to `page` mode and
patches only `orders`'s `children` box.
"""

import dash_mantine_components as dmc

from ui import feature_tags, rendered_badge


def default():
    return dmc.Card(
        dmc.Stack(
            [
                dmc.Title("No order selected", order=4),
                dmc.Text("Pick an order from the list. This is orders/[order_id]/default.py.", c="dimmed", size="sm"),
                feature_tags("default.py for omitted [order_id]"),
                rendered_badge(),
            ],
            align="center",
            justify="center",
            gap="xs",
            h="100%",
        ),
        withBorder=True,
        mih=490,
    )
