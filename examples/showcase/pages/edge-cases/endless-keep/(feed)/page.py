from collections.abc import AsyncIterator
from contextlib import suppress
from itertools import count
from typing import Any

import dash_mantine_components as dmc
from dash import set_props
from dash.exceptions import MissingCallbackContextException

from edge_helpers import edge_badge, edge_sleep, part_card, track_generator

TICK_ID = "edge-feed-tick"


async def page(**_: Any) -> AsyncIterator[Any]:
    url = "/edge-cases/endless-keep (feed)"
    with track_generator():
        yield part_card(
            "(feed) · endless generator",
            edge_badge("endless-keep-feed", url),
            dmc.Text("tick 0", id=TICK_ID, size="sm", ff="monospace"),
            dmc.Text("Ticks every 0.5 s until this slot is unmounted.", size="xs", c="dimmed"),
        )
        for tick in count(1):
            await edge_sleep(0.5)
            with suppress(MissingCallbackContextException):
                set_props(TICK_ID, {"children": f"tick {tick}"})
            yield None
