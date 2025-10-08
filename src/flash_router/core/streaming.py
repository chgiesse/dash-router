"""Async execution queue for streaming route rendering.

This module provides an :class:`ExecutionQueue` that walks an execution tree
of :class:`~flash_router.core.execution.ExecNode` objects.  Each node is
executed as soon as its parent has started streaming so that layout functions
implemented as async generators can progressively yield Server Sent Events
without breaking the parent/child hierarchy of the route tree.

The queue is designed to keep the hierarchical ordering of layouts while still
allowing descendants to start rendering as soon as their parents produced the
first chunk.  This mirrors the behaviour required for SSE responses where the
client must receive the parent container before any nested updates can be
applied.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from inspect import isasyncgen, isasyncgenfunction, isawaitable, iscoroutinefunction
from typing import Any, AsyncGenerator, Dict, Iterable, List, Optional

from dash import html
from dash.development.base_component import Component

from .execution import ExecNode
from ..components import ChildContainer, SlotContainer
from ..utils.helper_functions import _invoke_layout


@dataclass(frozen=True)
class StreamEvent:
    """Represents a single SSE payload produced by the queue."""

    node_id: str
    segment: str
    depth: int
    parent_id: Optional[str]
    payload: Any
    event_type: str = "layout"


class ExecutionQueue:
    """Execute an :class:`ExecNode` tree in a streaming friendly order."""

    _SENTINEL = object()

    def __init__(
        self,
        root: ExecNode,
        endpoint_results: Dict[str, Any],
    ) -> None:
        self._root = root
        self._endpoint_results = endpoint_results
        self._event_queue: "asyncio.Queue[Any]" = asyncio.Queue()
        self._pending_tasks = 0
        self._lock = asyncio.Lock()

    async def stream(self) -> AsyncGenerator[StreamEvent, None]:
        """Yield :class:`StreamEvent` objects in hierarchical order."""

        await self._increment_pending()
        asyncio.create_task(self._process_node(self._root, depth=0, parent_id=None))

        while True:
            event = await self._event_queue.get()
            if event is self._SENTINEL:
                break

            yield event

    async def _process_node(
        self,
        node: ExecNode,
        *,
        depth: int,
        parent_id: Optional[str],
    ) -> None:
        """Process a single node and enqueue its children when ready."""

        try:
            async for event in self._stream_node(node, depth=depth, parent_id=parent_id):
                await self._event_queue.put(event)
        finally:
            await self._decrement_pending()

    async def _stream_node(
        self,
        node: ExecNode,
        *,
        depth: int,
        parent_id: Optional[str],
    ) -> AsyncGenerator[StreamEvent, None]:
        data = self._endpoint_results.get(node.node_id)

        if node.is_lacy:
            loading_layout = await _invoke_layout(node.loading, **node.variables)
            yield StreamEvent(
                node_id=node.node_id,
                segment=node.segment,
                depth=depth,
                parent_id=parent_id,
                payload=loading_layout,
                event_type="lacy",
            )
            return

        if isinstance(data, Exception):
            layout = await node.handle_error(data, node.variables)
            yield StreamEvent(
                node_id=node.node_id,
                segment=node.segment,
                depth=depth,
                parent_id=parent_id,
                payload=layout,
                event_type="error",
            )
            return

        slot_placeholders, child_placeholder = self._build_placeholders(node)
        layout_kwargs = {
            **node.variables,
            **slot_placeholders,
            **child_placeholder,
            "data": data,
        }

        children = self._collect_children(node)
        has_scheduled_children = False

        try:
            layout_result = await self._invoke_for_stream(node.layout, **layout_kwargs)
        except Exception as exc:  # pragma: no cover - defensive
            layout_result = await node.handle_error(exc, node.variables)
            yield StreamEvent(
                node_id=node.node_id,
                segment=node.segment,
                depth=depth,
                parent_id=parent_id,
                payload=layout_result,
                event_type="error",
            )
            return

        async for chunk in self._iterate_layout(layout_result):
            if not has_scheduled_children and children:
                await self._schedule_children(children, depth=depth + 1, parent_id=node.node_id)
                has_scheduled_children = True

            yield StreamEvent(
                node_id=node.node_id,
                segment=node.segment,
                depth=depth,
                parent_id=parent_id,
                payload=chunk,
                event_type="layout",
            )

        if not has_scheduled_children and children:
            await self._schedule_children(children, depth=depth + 1, parent_id=node.node_id)

        yield StreamEvent(
            node_id=node.node_id,
            segment=node.segment,
            depth=depth,
            parent_id=parent_id,
            payload=None,
            event_type="complete",
        )

    async def _schedule_children(
        self,
        children: Iterable[ExecNode],
        *,
        depth: int,
        parent_id: str,
    ) -> None:
        children = list(children)
        if not children:
            return

        await self._increment_pending(len(children))
        for child in children:
            asyncio.create_task(
                self._process_node(child, depth=depth, parent_id=parent_id)
            )

    async def _invoke_for_stream(self, layout, **kwargs):
        if isasyncgenfunction(layout):
            return layout(**kwargs)

        if iscoroutinefunction(layout):
            return await layout(**kwargs)

        if callable(layout):
            result = layout(**kwargs)
        else:
            result = layout

        if isasyncgen(result):
            return result

        if isawaitable(result):
            return await result

        return result

    def _collect_children(self, node: ExecNode) -> List[ExecNode]:
        children: List[ExecNode] = []

        if isinstance(node.child_node, ExecNode):
            children.append(node.child_node)

        children.extend(node.slots.values())
        return children

    def _build_placeholders(self, node: ExecNode) -> tuple[Dict[str, Component], Dict[str, Component]]:
        slot_content: Dict[str, Component] = {}

        for slot_name, _slot_node in node.slots.items():
            clean_name = slot_name.strip("()")
            slot_content[clean_name] = SlotContainer(
                html.Div(className="dash-router-slot-loading"),
                node.node_id,
                slot_name,
                is_loaded=False,
            )

        if isinstance(node.child_node, ExecNode):
            child_layout = ChildContainer(
                html.Div(className="dash-router-child-loading"),
                node.node_id,
                node.child_node.segment,
            )
            return slot_content, {"children": child_layout}

        return slot_content, {}

    async def _iterate_layout(self, layout_result: Any) -> AsyncGenerator[Any, None]:
        if layout_result is None:
            yield None
            return

        if isasyncgen(layout_result):
            async for chunk in layout_result:
                yield chunk
            return

        if hasattr(layout_result, "__aiter__"):
            async for chunk in layout_result:
                yield chunk
            return

        if hasattr(layout_result, "__iter__") and not isinstance(layout_result, Component):
            for chunk in layout_result:
                yield chunk
            return

        yield layout_result

    async def _increment_pending(self, amount: int = 1) -> None:
        async with self._lock:
            self._pending_tasks += amount

    async def _decrement_pending(self) -> None:
        async with self._lock:
            self._pending_tasks -= 1
            pending = self._pending_tasks

        if pending == 0:
            await self._event_queue.put(self._SENTINEL)

