import dash_mantine_components as dmc

from dash_router import ChildContainer, RouteConfig
from ui import feature_tags, rendered_badge

config = RouteConfig(default_child="profile", title="Settings · Northwind Ops")


def page(children: ChildContainer, **_):
    return dmc.Stack(
        [
            dmc.Group(
                [
                    dmc.Stack([dmc.Title("Settings", order=2), feature_tags("navigate()", "url_for()", "query param on target")], gap=4),
                    rendered_badge("page rendered"),
                ],
                justify="space-between",
                align="flex-start",
            ),
            dmc.Box(children, maw=560),
        ]
    )
