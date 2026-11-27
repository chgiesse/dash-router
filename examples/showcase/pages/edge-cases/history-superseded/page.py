"""History superseded: `/edge-cases/history-superseded`, with the Slow and Fast links.

Click Slow (api.py 3 s), then Fast before Slow lands. The history must end `/edge-cases/history-superseded`
then `/edge-cases/history-superseded/fast`, with no Slow entry: while Slow's navigation is in flight, the
history guard turns the push of Fast into a replace of Slow's entry.
"""

import dash_mantine_components as dmc

from dash_router import ChildContainer, RouteConfig
from edge_helpers import case_card, edge_badge
from ui import link

URL = "/edge-cases/history-superseded"

config = RouteConfig(default_child="index")


def page(children: ChildContainer, **_):
    return case_card(
        URL,
        edge_badge("history-superseded", URL),
        dmc.Group(
            [
                link("Slow", f"{URL}/slow", size="sm"),
                link("Fast", f"{URL}/fast", size="sm"),
            ],
            gap="md",
        ),
        children,
    )
