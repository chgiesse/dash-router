"""Generator layout streaming rows into a fixed id.

Batch 1 and batch 2 render the same `edge-gen-table` id. Switching `?batch=` must cancel the batch 1
generator, so none of its `set_props` calls can reach the batch 2 table.
"""

from collections.abc import AsyncIterator
from contextlib import suppress
from typing import Any

import dash_mantine_components as dmc
from dash import set_props
from dash.exceptions import MissingCallbackContextException

from edge_helpers import case_card, edge_badge, edge_sleep, track_generator
from ui import link

TABLE_ID = "edge-gen-table"
URL = "/edge-cases/gen-fixed-id"


async def page(batch: str = "1", **_: Any) -> AsyncIterator[Any]:
    rows: list[Any] = []
    with track_generator():
        yield case_card(
            URL,
            edge_badge("gen-fixed-id", f"{URL}?batch={batch}"),
            dmc.Group(
                [
                    link("batch=1", f"{URL}?batch=1", size="sm"),
                    link("batch=2", f"{URL}?batch=2", size="sm"),
                ],
                gap="md",
            ),
            dmc.Text(f"batch {batch}: 8 rows, one every 0.4 s", size="xs", c="dimmed"),
            dmc.Stack([], id=TABLE_ID, gap=2),
        )
        for step in range(1, 9):
            await edge_sleep(0.4)
            rows.append(dmc.Text(f"batch {batch} · row {step}", size="sm", className="gen-row"))
            with suppress(MissingCallbackContextException):
                set_props(TABLE_ID, {"children": list(rows)})
            yield None
