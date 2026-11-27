"""Order summary: `[order_id]/summary/page.py`, the `default_child` of `[order_id]/page.py`.

`summary/api.py` feeds `data` to this page, and `summary/loading.py` is its skeleton while the order loads.
Because `summary` is the default (`UrlSegment(default="summary")` and `default_child="summary"`), `/orders/<id>`
renders this tab without waiting for `notes/`, and `notes/` renders at once without showing summary's skeleton.
"""

import dash_mantine_components as dmc

from ui import money, rendered_badge


def page(data: dict, **_):
    order, customer = data["order"], data["customer"]
    facts = [
        ("Status", order.status.value),
        ("Placed", order.placed.isoformat()),
        ("Items", str(order.items)),
        ("Total", money(order.total)),
        ("Customer segment", customer.segment),
    ]
    return dmc.Stack(
        [
            dmc.SimpleGrid(
                [
                    dmc.Paper(
                        [dmc.Text(k, size="xs", c="dimmed"), dmc.Text(v, fw=600)],
                        withBorder=True,
                        p="sm",
                    )
                    for k, v in facts
                ],
                cols={"base": 2, "md": 3},
            ),
            dmc.Group(
                [dmc.Text("summary/page.py · summary/api.py ≈ 2.0 s behind summary/loading.py", size="xs", c="dimmed"), rendered_badge()],
                justify="space-between",
            ),
        ]
    )
