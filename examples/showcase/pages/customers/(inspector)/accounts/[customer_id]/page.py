import dash_mantine_components as dmc

from data import Customer
from ui import rendered_badge


def page(data: Customer, customer_id: int, **_):
    color = "teal" if data.risk < 30 else "yellow" if data.risk <= 60 else "red"
    return dmc.Stack(
        [
            dmc.Text(f"Churn risk for customer #{customer_id}", size="sm"),
            dmc.Progress(value=data.risk, color=color, size="lg"),
            dmc.Group(
                [dmc.Badge(f"risk {data.risk}/100", color=color, variant="light"), rendered_badge()],
                justify="space-between",
            ),
            dmc.Text("(inspector)/accounts/[customer_id] parsed customer_id on its own cursor.", size="xs", c="dimmed"),
        ],
        gap="xs",
    )
