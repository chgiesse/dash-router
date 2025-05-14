from dash_router.core import loading_state
from ..utils.helper_functions import create_pathtemplate_key, _invoke_layout
from ..components import ChildContainer, LacyContainer, SlotContainer

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


@dataclass
class SyncExecNode:
    """Represents a node in the execution tree"""

    layout: Callable[..., Component] | Component
    segment: str
    node_id: UUID
    parent_segment: str
    loading_state: Dict[str, bool]
    path: str
    variables: Dict[str, str] = field(default_factory=dict)
    slots: Dict[str, "ExecNode"] = field(default_factory=dict)
    child_node: Dict[str, "ExecNode"] = field(default_factory=dict)
    path_template: str | None = None
    loading: Callable | Component | None = None
    error: Callable | Component | None = None

    def execute(self, is_init: bool = True) -> Component:
        """
        Executes the node by rendering its layout with the provided variables,
        slots, and views.
        """
        segment_key = self.segment

        if self.path_template:
            path_key = self.path_template.strip("<>")
            path_variable = self.variables.get(path_key)
            segment_key = create_pathtemplate_key(
                self.segment, self.path_template, path_variable, path_key
            )

        segment_loading_state = self.loading_state.get(segment_key, False)
        if self.loading is not None:
            if is_init and not segment_loading_state:
                self.loading_state[segment_key] = True
                if callable(self.loading):
                    loading_layout = self.loading()
                else:
                    loading_layout = self.loading

                return LacyContainer(loading_layout, str(self.node_id), self.variables)

        views_content = self._handle_child()
        slots_content = self._handle_slots()
        self.loading_state[segment_key] = True
        if callable(self.layout):
            try:
                layout = self.layout(**self.variables, **slots_content, **views_content)
            except Exception as e:
                layout = self.handle_error(e, self.variables)
            return layout

        return self.layout

    def handle_error(self, error: Exception, variables: Dict[str, any]):
        if self.error:
            if callable(self.error):
                layout = self.error(
                    error,
                    variables,
                )
                return layout
            return self.error
        return html.Div(str(error), className="banner")

    def _handle_slots(self) -> Dict[str, Component]:
        """
        Executes all slot nodes and gathers their rendered components.
        """
        if self.slots:
            views = [slot.execute() for slot in self.slots.values()]
            results = {}

            for slot_name, slot_layout in zip(self.slots.keys(), views):
                clean_slot_name = slot_name.strip("()")
                results[clean_slot_name] = SlotContainer(
                    slot_layout, self.node_id, slot_name
                )

            return results

        return {}

    def _handle_child(self) -> Dict[str, Component]:
        """
        Executes the current view node.
        """
        if self.child_node:
            _, child_node = next(iter(self.child_node.items()))
            layout = child_node.execute() if child_node else None
            return {
                "children": ChildContainer(
                    layout, self.node_id, child_node.segment if child_node else None
                )
            }

        return {}


class ExecTree:

    def __init__(
        self,
        variables,
        query_params,
        loading_state,
        request_pathname,
        endpoints,
        is_init,
    ) -> None:
        self.variables = variables
        self.query_params = query_params
        self.loading_state = loading_state
        self.request_pathname = request_pathname
        self.endpoints = endpoints
        self.is_init = is_init

    def build(self, current_node, segments: List[str]):
        """Recursively builds the execution tree for the matched route."""
        if not current_node:
            return current_node

    async def execute(self):
        pass

    def get_loading_state(self):
        pass

    def update_ls_value(self):
        pass

    def update_ls_state(self):
        pass
