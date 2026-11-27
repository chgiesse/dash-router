"""Shared helpers for the `/edge-cases` routes.

Lives next to `pages/` (not inside it) so the route loader never treats it as a route.
"""

import asyncio
import os
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from typing import Any, NamedTuple

import dash_mantine_components as dmc
from dash import Input, Output, State, callback, clientside_callback, dcc, html

from dash_router import RootContainer

EDGE_DELAY_SCALE = float(os.getenv("EDGE_DELAY_SCALE", "1.0"))
PID = os.getpid()

DEBUG_SERVER_ID = "edge-debug-server"
DEBUG_REFRESH_ID = "edge-debug-refresh"
DEBUG_TICK_ID = "edge-debug-tick"
DEBUG_LIVE_ID = "edge-debug-live"


class EdgeCase(NamedTuple):
    href: str
    label: str
    title: str
    expected: str


CASES: tuple[EdgeCase, ...] = (
    EdgeCase(
        "/edge-cases/superseded/slow",
        "Superseded · slow",
        "Superseded navigation (A)",
        "Slow (api.py 3.0 s) is started, then Fast is clicked before it lands. Slow must never render.",
    ),
    EdgeCase(
        "/edge-cases/superseded/fast",
        "Superseded · fast",
        "Superseded navigation (B)",
        "Fast (no api.py) renders at once and stays. The superseded Slow navigation is discarded.",
    ),
    EdgeCase(
        "/edge-cases/parent-loading",
        "Parent loading",
        "Lift while the parent loads",
        "Click Tab B in the parent's loading.py (api.py 3.0 s). The parent renders with tab-b selected.",
    ),
    EdgeCase(
        "/edge-cases/omitted-child?mode=blocked",
        "Omitted children",
        "Parent omits its children container",
        "mode=blocked omits children; mode=open renders them. Open + sub re-renders the parent.",
    ),
    EdgeCase(
        "/edge-cases/sibling-lazy?tag=a",
        "Sibling lazy",
        "Sibling slots, one lazy",
        "(left) is a lazy slot (api.py 3.0 s). Changing ?tag= only re-renders (right); (left) must not restart.",
    ),
    EdgeCase(
        "/edge-cases/lazy-race",
        "Lazy race",
        "Navigation while a lazy slot finishes",
        "The (lazy) slot (api.py 1.0 s) is near done when Next (api.py 1.5 s) is clicked. Both must land.",
    ),
    EdgeCase(
        "/edge-cases/lazy-replaced",
        "Lazy replaced",
        "Lazy boundary replaced by a sibling",
        "Slow (api.py 3.0 s) is replaced by Other after 0.5 s. Slow never lands and its stream aborts.",
    ),
    EdgeCase(
        "/edge-cases/gen-fixed-id?batch=1",
        "Generator, fixed id",
        "Generator streaming into a fixed id",
        "Batch 1 streams rows into a fixed table id. Switching to batch 2 cancels batch 1: no stale rows.",
    ),
    EdgeCase(
        "/edge-cases/endless-keep",
        "Endless keep",
        "Endless generator survives a sibling change",
        "(feed) ticks every 0.5 s. Switching ?panel= re-renders only (panel); the feed keeps running.",
    ),
    EdgeCase(
        "/edge-cases/endless-replace?mode=a",
        "Endless replace",
        "Endless generator replaced",
        "?mode=b closes the old generator and opens a new one (count stays 1). Leaving drops it to 0.",
    ),
    EdgeCase(
        "/edge-cases/gen-no-loading",
        "Generator, no loading.py",
        "Generator without a loading boundary",
        "Empty fallback for 0.3 s, then frame 1 is delivered.",
    ),
    EdgeCase(
        "/edge-cases/nested-lazy",
        "Nested lazy",
        "Nested loading boundaries",
        "Outer loading.py (api.py 1.2 s) contains an inner loading.py (api.py 1.5 s). Sub-links work during the outer load.",
    ),
    EdgeCase(
        "/edge-cases/slot-fallback/matched",
        "Slot fallback",
        "default.py versus an empty slot",
        "On /matched both slots render. On /other, (with-default) shows default.py and (no-default) renders empty.",
    ),
    EdgeCase(
        "/edge-cases/same-url",
        "Same URL",
        "Server navigate() to the current URL",
        "A server navigate() to the current URL must not re-render the page: the render counter stays the same.",
    ),
    EdgeCase(
        "/edge-cases/errors",
        "Errors",
        "Error boundaries in slots",
        "(api-err) fails after 0.5 s in a lazy slot; (gen-err) yields frame 1 then fails. Each shows its own error.py.",
    ),
    EdgeCase(
        "/edge-cases/history/one",
        "History",
        "Rapid back / forward",
        "Walk one → two → three, then history.back() twice and history.forward() twice in quick succession.",
    ),
    EdgeCase(
        "/edge-cases/plain-set-props",
        "Plain set_props",
        "Plain callback, superseded set_props",
        "Slow (2 s) then Fast: the superseded slow callback's set_props must not overwrite fresh-fast.",
    ),
    EdgeCase(
        "/edge-cases/history-superseded",
        "History superseded",
        "Superseded navigation in history",
        "Slow (api.py 3 s) then Fast before Slow lands: history ends at the index, then Fast. No Slow entry.",
    ),
    EdgeCase(
        "/edge-cases/tabs-segment",
        "Tabs in the URL",
        "UrlSegment tabs",
        "Tab A is the default (bare URL). Clicking B or C pushes its URL; back and forward select the tab again.",
    ),
)


async def edge_sleep(seconds: float) -> None:
    await asyncio.sleep(seconds * EDGE_DELAY_SCALE)


_renders: dict[str, int] = {}
_last_render = ""
_active_generators = 0


def record_render(node_key: str, url: str) -> int:
    """Count one render of `node_key` in this process and return the new total."""
    global _last_render
    _renders[node_key] = _renders.get(node_key, 0) + 1
    _last_render = f"{node_key} {url}"
    return _renders[node_key]


@contextmanager
def track_generator() -> Iterator[None]:
    """Count a streaming layout while it runs. Closing the generator (navigating away) runs `finally`."""
    global _active_generators
    _active_generators += 1
    try:
        yield
    finally:
        _active_generators -= 1


def active_generators() -> int:
    return _active_generators


def edge_badge(node_key: str, url: str, *, count: int | None = None, pid: int = PID) -> dmc.Badge:
    """Badge with the URL, render count, pid and server time. Its id is `edge-badge-<node_key>`."""
    renders = record_render(node_key, url) if count is None else count
    stamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    return dmc.Badge(
        f"{url} · render #{renders} · pid {pid} · {stamp}",
        id=f"edge-badge-{node_key}",
        variant="light",
        color="gray",
        size="sm",
        radius="sm",
        style={"textTransform": "none", "fontFamily": "monospace"},
    )


def part_card(title: str, badge: dmc.Badge, *body: Any) -> dmc.Card:
    return dmc.Card(
        [
            dmc.Group([dmc.Text(title, fw=600), badge], justify="space-between", align="flex-start", mb="xs"),
            dmc.Stack(list(body), gap="xs"),
        ],
        withBorder=True,
        radius="md",
        padding="md",
    )


def case_card(path: str, badge: dmc.Badge, *body: Any) -> dmc.Card:
    """Card for the route that is a case entry point: title and expected behaviour come from `CASES`."""
    case = next(c for c in CASES if c.href.split("?")[0] == path)
    return dmc.Card(
        [
            dmc.Group(
                [
                    dmc.Stack(
                        [dmc.Text(case.title, fw=600), dmc.Text(f"Expected: {case.expected}", size="sm", c="dimmed")],
                        gap=4,
                    ),
                    badge,
                ],
                justify="space-between",
                align="flex-start",
                mb="sm",
            ),
            dmc.Stack(list(body), gap="sm"),
        ],
        withBorder=True,
        radius="md",
        padding="md",
    )


def _server_snapshot() -> str:
    return (
        f"pid {PID} · EDGE_DELAY_SCALE {EDGE_DELAY_SCALE:g} · "
        f"active generators {_active_generators} · last render: {_last_render or '-'}"
    )


def debug_panel() -> dmc.Card:
    return dmc.Card(
        [
            dmc.Group(
                [
                    dmc.Text("Debug · this worker", fw=600, size="sm"),
                    dmc.Button("Refresh server counts", id=DEBUG_REFRESH_ID, size="xs", variant="light"),
                ],
                justify="space-between",
            ),
            dmc.Text(_server_snapshot(), id=DEBUG_SERVER_ID, size="xs", ff="monospace"),
            html.Pre(id=DEBUG_LIVE_ID, children="…", style={"fontSize": "11px", "margin": 0}),
            dcc.Interval(id=DEBUG_TICK_ID, interval=500),
        ],
        withBorder=True,
        radius="md",
        padding="sm",
    )


@callback(Output(DEBUG_SERVER_ID, "children"), Input(DEBUG_REFRESH_ID, "n_clicks"), prevent_initial_call=True)
def refresh_debug_server(_: int | None) -> str:
    return _server_snapshot()


clientside_callback(
    """
    function(n, committed) {
        const containers = [];
        const lazy = [];
        for (const el of document.querySelectorAll('[id]')) {
            if (!el.id.includes('DASH-ROUTER-')) continue;
            try {
                const parsed = JSON.parse(el.id);
                (parsed.type === 'DASH-ROUTER-LAZY' ? lazy : containers).push(parsed.index);
            } catch (e) {}
        }
        return JSON.stringify({committed: committed, containers: containers.sort(), lazy: lazy.sort()}, null, 2);
    }
    """,
    Output(DEBUG_LIVE_ID, "children"),
    Input(DEBUG_TICK_ID, "n_intervals"),
    State(RootContainer.ids.committed_store, "data"),
)
