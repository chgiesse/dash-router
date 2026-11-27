import dash_mantine_components as dmc

from ui import feature_tags, graph_spinner, loading_badge

# Replaces only the chart: the range selector stays mounted in `overview/page.py`.
loading = dmc.Stack(
    [
        dmc.Group(
            [
                feature_tags("(revenue)/api.py ≈ 2.5 s", "typed query param `range`", "Patch every 1 s"),
                loading_badge(),
            ],
            justify="space-between",
        ),
        graph_spinner("Loading revenue chart…", height=240),
    ],
    gap="sm",
)
