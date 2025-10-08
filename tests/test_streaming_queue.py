import asyncio

import pytest

pytest.importorskip("dash")
from dash import html

from flash_router.core.execution import ExecNode
from flash_router.core.streaming import ExecutionQueue, StreamEvent


async def _collect_events(queue: ExecutionQueue) -> list[StreamEvent]:
    events = []
    async for event in queue.stream():
        events.append(event)
    return events


@pytest.mark.asyncio
async def test_queue_preserves_hierarchy():
    async def root_layout(data, children, slot_one):
        yield html.Div("root-start")
        await asyncio.sleep(0)
        yield html.Div([children, slot_one])

    async def child_layout(data):
        await asyncio.sleep(0)
        return html.Div(f"child-{data}")

    def slot_layout(data):
        return html.Div(f"slot-{data}")

    root = ExecNode(
        segment="root",
        node_id="root",
        parent_id="",
        layout=root_layout,
        variables={},
    )

    child = ExecNode(
        segment="child",
        node_id="child",
        parent_id="root",
        layout=child_layout,
        variables={},
    )

    slot = ExecNode(
        segment="slot",
        node_id="slot",
        parent_id="root",
        layout=slot_layout,
        variables={},
    )

    root.child_node = child
    root.slots = {"(slot_one)": slot}

    endpoint_results = {
        "root": {"value": 1},
        "child": "payload",
        "slot": "slot-payload",
    }

    queue = ExecutionQueue(root, endpoint_results)
    events = await _collect_events(queue)

    root_layout_indices = [
        idx for idx, event in enumerate(events) if event.node_id == "root" and event.event_type == "layout"
    ]
    child_layout_indices = [
        idx for idx, event in enumerate(events) if event.node_id == "child" and event.event_type == "layout"
    ]
    slot_layout_indices = [
        idx for idx, event in enumerate(events) if event.node_id == "slot" and event.event_type == "layout"
    ]

    assert root_layout_indices, "root layout events should be emitted"
    assert child_layout_indices and slot_layout_indices
    assert root_layout_indices[0] < child_layout_indices[0]
    assert root_layout_indices[0] < slot_layout_indices[0]

    # Ensure completion events are emitted for each node
    completed_nodes = {event.node_id for event in events if event.event_type == "complete"}
    assert completed_nodes == {"root", "child", "slot"}


@pytest.mark.asyncio
async def test_queue_handles_lazy_nodes():
    async def root_layout(data, children):
        yield html.Div("root")
        yield html.Div(children)

    def loading_layout(**_):
        return html.Div("loading")

    async def lazy_layout(data):
        await asyncio.sleep(0)
        return html.Div(f"resolved-{data}")

    root = ExecNode(
        segment="root",
        node_id="root",
        parent_id="",
        layout=root_layout,
        variables={},
    )

    lazy_node = ExecNode(
        segment="lazy",
        node_id="lazy",
        parent_id="root",
        layout=lazy_layout,
        variables={},
        loading=loading_layout,
        is_lacy=True,
    )

    root.child_node = lazy_node

    endpoint_results = {
        "root": "root-data",
        "lazy": "lazy-data",
    }

    queue = ExecutionQueue(root, endpoint_results)
    events = await _collect_events(queue)

    lazy_events = [event for event in events if event.node_id == "lazy"]

    assert lazy_events[0].event_type == "lacy"
    assert isinstance(lazy_events[0].payload.children, html.Div)

    layout_events = [event for event in lazy_events if event.event_type == "layout"]
    assert layout_events, "lazy node should eventually stream its real layout"
    assert layout_events[0].payload.children == "resolved-lazy-data"

    assert any(event.event_type == "complete" for event in lazy_events)

