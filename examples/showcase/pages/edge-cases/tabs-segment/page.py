"""Tabs in the URL: `UrlSegment` binds the tab bar to the path segment after this route.

Tab A (`default_child="a"`) is the default, so the bare `/edge-cases/tabs-segment` stands for it. Clicking a
tab pushes its URL. Back and forward select the tab again. There is no callback: the router syncs the tab bar
with the URL.
"""

import dash_mantine_components as dmc

from dash_router import ChildContainer, RouteConfig, UrlSegment
from edge_helpers import case_card, edge_badge

URL = "/edge-cases/tabs-segment"

config = RouteConfig(default_child="a")


def page(children: ChildContainer, **_):
    tabs = dmc.Tabs(
        dmc.TabsList([dmc.TabsTab(f"Tab {value.upper()}", value=value) for value in ("a", "b", "c")]),
        id="edge-tabs-segment",
    )
    return case_card(URL, edge_badge("tabs-segment", URL), UrlSegment(tabs, children, default="a"), children)
