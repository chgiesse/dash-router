from collections.abc import AsyncIterator
from contextlib import suppress
from itertools import count
from typing import Any

from dash import set_props
from dash.exceptions import MissingCallbackContextException

from edge_helpers import edge_badge, edge_sleep, part_card, track_generator

TICK_ID = "edge-stream-tick"


async def page(mode: str = "a", **_: Any) -> AsyncIterator[Any]:
    url = f"/edge-cases/endless-replace?mode={mode}"
    with track_generator():
        yield part_card(
            f"(stream) · mode={mode}",
            edge_badge("endless-replace-stream", url),
            f"tick 0 (mode={mode})",
        )
        for tick in count(1):
            await edge_sleep(0.5)
            with suppress(MissingCallbackContextException):
                set_props(TICK_ID, {"children": f"tick {tick} (mode={mode})"})
            yield None
