import dash_mantine_components as dmc

from data import CUSTOMERS
from ui import rendered_badge


def page(customer_id: int, **_):
    customer = CUSTOMERS[customer_id]
    return dmc.Stack(
        [
            dmc.Text(f"Pinned: {customer.name}", fw=600),
            dmc.Text(f"{customer.city} · {customer.segment}", size="sm", c="dimmed"),
            dmc.Group([dmc.Text("Now open Insights from the tabs above.", size="xs", c="dimmed"), rendered_badge()], justify="space-between"),
        ],
        gap=4,
    )
