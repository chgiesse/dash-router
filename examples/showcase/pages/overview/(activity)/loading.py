import dash_mantine_components as dmc

from ui import SkeletonColumn, loading_section, table_skeleton

_COLUMNS = [
    SkeletonColumn("Order", width="18%", kind="id", widths=(46, 48, 44, 50, 46, 48)),
    SkeletonColumn("Customer", width="44%", kind="text", widths=("72%", "56%", "84%", "64%", "78%", "60%")),
    SkeletonColumn("Status", width="18%", kind="pill", widths=(66, 58, 72, 62, 68, 56)),
    SkeletonColumn("Placed", width="20%", kind="text", widths=(82, 82, 82, 82, 82, 82)),
]

loading = loading_section(
    "Recent activity · (activity)/api.py ≈ 3.5 s",
    dmc.Stack(
        [
            table_skeleton(_COLUMNS, rows=6),
            dmc.Group(
                [
                    dmc.Skeleton(height=14, width=185, radius="sm"),
                    dmc.Skeleton(height=14, width=115, radius="sm"),
                ],
                gap="xs",
            ),
        ]
    ),
    features=("slowest slot", "error.py boundary"),
    mih=404,
)
