import dash_mantine_components as dmc

from ui import loading_badge

loading = dmc.Stack(
    [
        dmc.Skeleton(height=15, width=185, radius="sm"),
        dmc.Skeleton(height=12, radius="xl"),
        dmc.Group(
            [
                dmc.Skeleton(height=20, width=78, radius="xl"),
                loading_badge(),
            ],
            justify="space-between",
        ),
        dmc.Text("(inspector)/accounts/[customer_id] parsed customer_id on its own cursor.", size="xs", c="dimmed"),
    ],
    gap="xs",
)
