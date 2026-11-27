import dash_mantine_components as dmc

from ui import kpi_card, rendered_badge


def page(data: dict, **_):
    return dmc.Stack(
        [
            dmc.Group(
                [dmc.Text("KPIs · (kpis)/api.py ≈ 1.5 s", size="sm", fw=600), rendered_badge()],
                justify="space-between",
            ),
            dmc.SimpleGrid(
                [
                    kpi_card("Orders", data["orders"], "indigo"),
                    kpi_card("Open", data["open"], "blue"),
                    kpi_card("Delayed", data["delayed"], "orange"),
                    kpi_card("Revenue", data["revenue"], "teal", currency=True),
                ],
                cols={"base": 2, "md": 4},
            ),
        ],
        gap="xs",
    )
