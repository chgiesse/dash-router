import dash_mantine_components as dmc

from dash_router import ChildContainer, RouteConfig
from edge_helpers import case_card, edge_badge
from ui import link

config = RouteConfig(title="Omitted children · Northwind Ops")


def page(children: ChildContainer, mode: str = "open", **_):
    url = f"/edge-cases/omitted-child?mode={mode}"
    body: list = [
        dmc.Group(
            [
                link("mode=blocked", "/edge-cases/omitted-child?mode=blocked", size="sm"),
                link("mode=open", "/edge-cases/omitted-child?mode=open", size="sm"),
                link("open + sub", "/edge-cases/omitted-child/sub?mode=open", size="sm"),
            ],
            gap="md",
        ),
        dmc.Text(f"mode={mode}: children {'omitted' if mode == 'blocked' else 'rendered'}.", size="sm", c="dimmed"),
    ]
    if mode != "blocked":
        body.append(children)
    return case_card("/edge-cases/omitted-child", edge_badge("omitted-child", url), *body)
