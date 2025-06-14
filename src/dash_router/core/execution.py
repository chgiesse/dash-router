from dash_router.core import loading_state
from ..utils.helper_functions import create_pathtemplate_key, _invoke_layout
from ..components import ChildContainer, LacyContainer, SlotContainer
from .routing_context import RoutingContext

from dataclasses import dataclass, field
from typing import Callable, Dict, Awaitable, Literal, List
from uuid import UUID
import asyncio

from dash import html
from dash.development.base_component import Component


LoadingStateType = Literal["lacy", "done", "hidden"] | None


@dataclass
class ExecNode:
    """Represents a node in the execution tree"""

    segment: str
    node_id: str
    parent_id: str
    layout: Callable[..., Awaitable[Component]] | Component
    variables: Dict[str, str] = field(default_factory=dict)
    slots: Dict[str, "ExecNode"] = field(default_factory=dict)
    child_node: Dict[str, "ExecNode"] = field(default_factory=dict)
    loading: Callable | Component | None = None
    error: Callable | Component | None = None
    is_lacy: bool = False

    async def execute(
        self, endpoint_results: Dict[UUID, Dict[any, any]], is_init: bool = True
    ) -> Component:
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
            self._handle_slots(is_init, endpoint_results),
            self._handle_child(is_init, endpoint_results),
        )

        all_kwargs = {**self.variables, **slots_content, **views_content, "data": data}

        try:
            layout = await _invoke_layout(self.layout, **all_kwargs)
        except Exception as e:
            layout = await self.handle_error(e, self.variables)

        return layout

    async def handle_error(self, error: Exception, variables: Dict[str, any]):
        if not self.error:
            return html.Div(str(error), className="banner")

        error_layout = await _invoke_layout(self.error, error, **variables)
        return error_layout

    async def _handle_slots(
        self, is_init: bool, endpoint_results: Dict[UUID, Dict[any, any]]
    ) -> Dict[str, Component]:
        """Executes all slot nodes and gathers their rendered components."""
        if not self.slots:
            return {}

        executables = [
            slot.execute(endpoint_results, is_init) for slot in self.slots.values()
        ]
        views = await asyncio.gather(*executables)
        results = {}

        for slot_name, slot_layout in zip(self.slots.keys(), views):
            clean_slot_name = slot_name.strip("()")
            results[clean_slot_name] = SlotContainer(
                slot_layout, self.segment, slot_name
            )

        return results

    async def _handle_child(
        self, is_init: bool, endpoint_results: Dict[UUID, Dict[any, any]]
    ) -> Dict[str, Component]:
        """Executes the current view node."""
        if not self.child_node:
            return {}

        _, child_node = next(iter(self.child_node.items()))
        layout = (
            await child_node.execute(endpoint_results, is_init) if child_node else None
        )
        return {
            "children": ChildContainer(
                layout, self.node_id, child_node.segment if child_node else None
            )
        }
