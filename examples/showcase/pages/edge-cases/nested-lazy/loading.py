import dash_mantine_components as dmc

from ui import link, loading_section, skeleton_block

loading = loading_section(
    "Outer loading · nested-lazy/api.py 1.2 s",
    dmc.Stack(
        [
            skeleton_block(2),
            dmc.Group(
                [
                    link("one", "/edge-cases/nested-lazy/one", size="sm"),
                    link("two", "/edge-cases/nested-lazy/two", size="sm"),
                ],
                gap="md",
            ),
        ],
        gap="sm",
    ),
)
