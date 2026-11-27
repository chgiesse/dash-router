"""`/docs` itself: the catch-all matched zero segments, so its default.py renders."""

import dash_mantine_components as dmc

from ui import link, section


def default(**_):
    return section(
        "Welcome to the knowledge base",
        dmc.Stack(
            [
                dmc.Text("Pick an article on the left, or jump straight to a deep link:", size="sm"),
                link("/docs/fulfilment/shipping/returns", "/docs/fulfilment/shipping/returns", size="sm"),
                link("/docs/fulfilment/shipping/does-not-exist", "/docs/fulfilment/shipping/does-not-exist", size="sm"),
            ],
            gap="xs",
        ),
        features=("[__rest]/default.py",),
    )
