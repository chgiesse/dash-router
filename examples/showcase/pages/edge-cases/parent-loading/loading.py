import dash_mantine_components as dmc

from ui import link, loading_section, skeleton_block

loading = loading_section(
    "Parent loading · parent/api.py 3.0 s",
    dmc.Stack(
        [
            skeleton_block(3),
            dmc.Text("Click a tab while the parent is still loading:", size="sm", c="dimmed"),
            dmc.Group(
                [
                    link("Tab A", "/edge-cases/parent-loading/tab-a", size="sm"),
                    link("Tab B", "/edge-cases/parent-loading/tab-b", size="sm"),
                ],
                gap="md",
            ),
        ],
        gap="sm",
    ),
)
