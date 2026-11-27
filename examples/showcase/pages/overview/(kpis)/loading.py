import dash_mantine_components as dmc

from ui import kpi_card, loading_badge

# Same structure as page.py, so the numbers roll up from 0 once (kpis)/api.py returns.
loading = dmc.Stack(
    [
        dmc.Group(
            [dmc.Text("KPIs · (kpis)/api.py ≈ 1.5 s", size="sm", fw=600), loading_badge()],
            justify="space-between",
        ),
        dmc.SimpleGrid(
            [
                kpi_card("Orders", 0),
                kpi_card("Open", 0),
                kpi_card("Delayed", 0),
                kpi_card("Revenue", 0, currency=True),
            ],
            cols={"base": 2, "md": 4},
        ),
    ],
    gap="xs",
)
