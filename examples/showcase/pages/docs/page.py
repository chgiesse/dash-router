"""Knowledge base shell: a static sidebar plus one catch-all child for any depth of article."""

import dash_mantine_components as dmc

from dash_router import ChildContainer, RouteConfig
from data import DOCS
from ui import feature_tags, rendered_badge

config = RouteConfig(title="Knowledge base · Northwind Ops")


def _tree(node: dict, prefix: str) -> list:
    items = []
    for key, value in node.items():
        if key.startswith("_") or not isinstance(value, dict):
            continue
        href = f"{prefix}/{key}"
        items.append(
            dmc.NavLink(
                label=str(value.get("_title", key)),
                href=href,
                children=_tree(value, href) or None,
                opened=True,
                childrenOffset=14,
            )
        )
    return items


def page(children: ChildContainer, **_):
    return dmc.Stack(
        [
            dmc.Group(
                [
                    dmc.Stack([dmc.Title("Knowledge base", order=2), feature_tags("[__rest] catch-all", "default.py at /docs")], gap=4),
                    rendered_badge("page rendered"),
                ],
                justify="space-between",
                align="flex-start",
            ),
            dmc.Grid(
                [
                    dmc.GridCol(dmc.Card(_tree(DOCS, "/docs"), withBorder=True, p="xs"), span={"base": 12, "md": 4}),
                    dmc.GridCol(dmc.Box(children, mih=300), span={"base": 12, "md": 8}),
                ]
            ),
        ]
    )
