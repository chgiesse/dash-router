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

