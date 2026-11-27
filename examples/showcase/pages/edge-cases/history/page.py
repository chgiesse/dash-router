import dash_mantine_components as dmc

from dash_router import ChildContainer
from edge_helpers import edge_badge
from ui import link


def page(children: ChildContainer, **_):
    return dmc.Stack(
        [
            dmc.Group(
                [
                    edge_badge("history", "/edge-cases/history"),
                    link("one", "/edge-cases/history/one", size="sm"),
                    link("two", "/edge-cases/history/two", size="sm"),
                    link("three", "/edge-cases/history/three", size="sm"),
                ],
                gap="md",
            ),
            children,
        ],
        gap="sm",
    )
