"""Documentation shell: a static sidebar with one NavLink per doc page, plus one child for the page itself."""

import dash_mantine_components as dmc

from dash_router import ChildContainer, RouteConfig
from docs_site import DOC_PAGES, doc_href
from ui import feature_tags, rendered_badge

config = RouteConfig(title="Documentation · Northwind Ops")


def page(children: ChildContainer, **_):
    sidebar = dmc.Stack(
        [
            dmc.NavLink(label=page.title, href=doc_href(page.slug), active="exact", variant="light")
            for page in DOC_PAGES
        ],
        gap=2,
    )
    return dmc.Stack(
        [
            dmc.Group(
                [
                    dmc.Stack(
                        [
                            dmc.Title("Documentation", order=2),
                            feature_tags("[param] omitted state", "NavLink active state"),
                        ],
                        gap=4,
                    ),
                    rendered_badge("page rendered"),
                ],
                justify="space-between",
                align="flex-start",
            ),
            dmc.Grid(
                [
                    dmc.GridCol(dmc.Card(sidebar, withBorder=True, radius="md", p="xs"), span={"base": 12, "md": 3}),
                    dmc.GridCol(dmc.Box(children, mih=540), span={"base": 12, "md": 9}),
                ]
            ),
        ]
    )

