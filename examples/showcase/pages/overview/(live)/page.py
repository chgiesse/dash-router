"""Live feed: a generator `page` streaming incremental updates via `Patch` + `set_props`.

No callback is needed: `page` yields the feed shell for Frame 0, then suspends and
flushes `LiveFeed.add_event(...)` updates (`set_props` + `Patch`) on each `yield`.
Navigating away cancels and closes the generator automatically.
"""

import asyncio
import random
from contextlib import suppress
from datetime import datetime

import dash_mantine_components as dmc
from dash import Patch, set_props
from dash.exceptions import MissingCallbackContextException

from data import CUSTOMERS
from ui import section


class LiveFeed(dmc.Card):
    class ids:
        feed = "live-feed"
        status = "live-feed-status"

    def __init__(self) -> None:
        card = section(
            "Live orders",
            dmc.Stack(
                [
                    dmc.Text("connecting…", id=self.ids.status, size="xs", c="dimmed"),
                    dmc.ScrollArea(dmc.Stack([], id=self.ids.feed, gap=6), h=256),
                ],
                gap="xs",
            ),
            features=("generator layout", "Patch + set_props"),
            h="100%",
        )
        super().__init__(
            children=card.children,
            withBorder=True,
            radius="md",
            padding="md",
            h="100%",
        )

    @classmethod
    def add_event(cls, customer_name: str, amount: int, count: int, total: int = 8) -> None:
        entry = dmc.Group(
            [
                dmc.Badge(datetime.now().strftime("%H:%M:%S"), variant="light", size="sm"),
                dmc.Text(f"{customer_name} · ${amount}", size="sm"),
            ],
            gap="xs",
            className="live-feed-item",
        )
        feed = Patch()
        feed.prepend(entry)
        with suppress(MissingCallbackContextException):
            set_props(cls.ids.feed, {"children": feed})
            set_props(cls.ids.status, {"children": f"streamed {count}/{total} events"})


async def page(**_):
    yield LiveFeed()

    rng = random.Random()
    for n in range(1, 9):
        await asyncio.sleep(1.2 if n > 1 else 0.3)
        customer = rng.choice(list(CUSTOMERS.values()))
        yield LiveFeed.add_event(customer.name, rng.randint(40, 900), n)
