import dash_mantine_components as dmc

from data import CUSTOMERS
from ui import section


def page(**_):
    buckets = {"low (<30)": 0, "medium (30-60)": 0, "high (>60)": 0}
    for c in CUSTOMERS.values():
        key = "low (<30)" if c.risk < 30 else "medium (30-60)" if c.risk <= 60 else "high (>60)"
        buckets[key] += 1
    return section(
        "Insights · churn risk",
        dmc.Stack(
            [
                dmc.BarChart(
                    h=220,
                    data=[{"bucket": k, "Customers": v} for k, v in buckets.items()],
                    dataKey="bucket",
                    series=[{"name": "Customers", "color": "indigo.6"}],
                    barProps={"isAnimationActive": True, "animationDuration": 600, "animationEasing": "ease-out"},
                ),
                dmc.Alert(
                    "(pinned) has no `insights` route and no default.py, so it renders empty here, on a soft "
                    "navigation and on a reload alike. Add (pinned)/default.py to show a fallback instead.",
                    color="blue",
                    variant="light",
                ),
            ]
        ),
        features=("(inspector) -> default.py", "(pinned) empty"),
    )
