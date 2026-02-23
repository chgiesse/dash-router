from click import Option
from ..utils.helper_functions import _invoke_layout
from ..components import ChildContainer, LacyContainer, SlotContainer
from collections.abc import Awaitable, Callable

from dataclasses import dataclass, field
from typing import Any, Optional
from uuid import UUID
import asyncio

from dash import html
from dash.development.base_component import Component


@dataclass
class ExecNode:
    """Represents a node in the execution tree"""

    segment: str
    node_id: str
    parent_id: str
    layout: Callable[..., Awaitable[Component]] | Component
    variables: dict[str, str] = field(default_factory=dict)
    slots: dict[str, "ExecNode"] = field(default_factory=dict)
    child_node: Optional["ExecNode"] = "default"
    loading: Optional[Callable | Component] = None
    error: Optional[Callable | Component] = None
    is_lacy: bool = False

    async def execute(self, endpoint_results: dict[UUID, dict[any, any]]) -> Component:
        """
        Executes the node by rendering its layout with the provided variables,
        slots, and views.
        """
        data = endpoint_results.get(self.node_id)

        if self.is_lacy:
            loading_layout = await _invoke_layout(self.loading, **self.variables)
            return LacyContainer(loading_layout, str(self.node_id), self.variables)

        if isinstance(data, Exception):
            return await self.handle_error(data, self.variables)

        slots_content, views_content = await asyncio.gather(
            self._handle_slots(endpoint_results),
            self._handle_child(endpoint_results),
        )

        all_kwargs = {**self.variables, **slots_content, **views_content, "data": data}

        try:
            layout = await _invoke_layout(self.layout, **all_kwargs)
        except Exception as e:
            layout = await self.handle_error(e, self.variables)

        return layout

    async def handle_error(self, error: Exception, variables: dict[str, Any]):
        if not self.error:
            return html.Div(str(error), className="banner")

        error_layout = await _invoke_layout(self.error, error, **variables)
        return error_layout

    async def _handle_slots(
        self, endpoint_results: dict[UUID, dict[Any, Any]]
    ) -> dict[str, Component]:
        """Executes all slot nodes and gathers their rendered components."""
        if not self.slots:
            return {}

        executables = [slot.execute(endpoint_results) for slot in self.slots.values()]
        views = await asyncio.gather(*executables)
        results = {}

        for slot_name, slot_layout in zip(self.slots.keys(), views):
            clean_slot_name = slot_name.strip("()")
            results[clean_slot_name] = SlotContainer(
                slot_layout, self.node_id, slot_name
            )

        return results

    async def _handle_child(
        self, endpoint_results: dict[UUID, dict[Any, Any]]
    ) -> dict[str, Component]:
        """Executes the current view node."""
        if self.child_node == "default":
            return {}

        layout = await self.child_node.execute(endpoint_results) if self.child_node else None

        return {
            "children": ChildContainer(
                layout, self.node_id, self.child_node.segment if self.child_node else None
            )
        }
