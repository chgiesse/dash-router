import dash_mantine_components as dmc

from ui import SkeletonColumn, loading_section, table_skeleton

_COLUMNS = [
    SkeletonColumn("Order", width="18%", kind="id", widths=(46, 48, 44, 50)),
    SkeletonColumn("Placed", width="30%", kind="text", widths=(82, 82, 82, 82)),
    SkeletonColumn("Status", width="26%", kind="text", widths=(58, 66, 54, 62)),
    SkeletonColumn("Total", width="26%", kind="number", align="right", widths=(64, 56, 70, 60)),
]

loading = loading_section(
    dmc.Skeleton(height=22, width=190, radius="sm"),
    dmc.Stack(
        [
            dmc.Skeleton(height=15, width="62%", radius="sm"),
            table_skeleton(_COLUMNS, rows=4, vertical_spacing=6, fade_tail=False),
            dmc.Group(
                [
                    dmc.Skeleton(height=14, width=74, radius="sm"),
                    dmc.Skeleton(height=14, width=52, radius="sm"),
                ],
                justify="space-between",
            ),
        ]
    ),
    features=("main branch: accounts/[customer_id]",),
)
