from collections.abc import AsyncIterator
from typing import Any

import dash_mantine_components as dmc

from edge_helpers import case_card, edge_badge, edge_sleep

URL = "/edge-cases/gen-no-loading"


async def page(**_: Any) -> AsyncIterator[Any]:
    await edge_sleep(0.3)
    yield case_card(
        URL,
        edge_badge("gen-no-loading", URL),
        dmc.Text("Frame 1 delivered after 0.3 s. There is no loading.py, so the fallback was empty.", size="sm"),
    )
