from click import Option
from ..utils.helper_functions import _invoke_layout
from ..components import ChildContainer, LacyContainer, SlotContainer

from dataclasses import dataclass, field
from typing import Any, AnyStr, Callable, Dict, Optional
from uuid import UUID

from dash import html
from dash.development.base_component import Component


@dataclass
class ExecNode:
    """Represents a node in the execution tree"""

    segment: str
    node_id: str
    parent_id: str
    layout: Callable[..., Component] | Component
    variables: Dict[str, str] = field(default_factory=dict)
    slots: Dict[str, "ExecNode"] = field(default_factory=dict)
    child_node: Optional["ExecNode"] = "default"
    loading: Optional[Callable | Component] = None
    error: Optional[Callable | Component] = None
    is_lacy: bool = False

    def execute(self, endpoint_results: Dict[UUID, Dict[str, Any]]) -> Component:
        """
        Executes the node by rendering its layout with the provided variables,
        slots, and views.
        """
        data = endpoint_results.get(self.node_id)

        if self.is_lacy:
            loading_layout = _invoke_layout(self.loading, **self.variables)
            return LacyContainer(loading_layout, str(self.node_id), self.variables)

        if isinstance(data, Exception):
            return self.handle_error(data, self.variables)

        slots_content = self._handle_slots(endpoint_results)
        views_content = self._handle_child(endpoint_results)

        all_kwargs = {**self.variables, **slots_content, **views_content, "data": data}

        try:
            layout = _invoke_layout(self.layout, **all_kwargs)
        except Exception as e:
            layout = self.handle_error(e, self.variables)

        return layout

    def handle_error(self, error: Exception, variables: Dict[str, Any]):
        if not self.error:
            return html.Div(str(error), className="banner")

        error_layout = _invoke_layout(self.error, error, **variables)
        return error_layout

    def _handle_slots(
        self, endpoint_results: Dict[UUID, Dict]
    ) -> Dict[str, Component]:
        """Executes all slot nodes and gathers their rendered components."""
        if not self.slots:
            return {}

        results = {}
        for slot_name, slot_node in self.slots.items():
            slot_layout = slot_node.execute(endpoint_results)
            clean_slot_name = slot_name.strip("()")
            results[clean_slot_name] = SlotContainer(
                slot_layout, self.node_id, slot_name
            )

        return results

    def _handle_child(
        self, endpoint_results: Dict[UUID, Dict]
    ) -> Dict[str, Component]:
        """Executes the current view node."""
        if self.child_node == "default":
            return {}

        layout = self.child_node.execute(endpoint_results) if self.child_node else None

        return {
            "children": ChildContainer(
                layout, self.node_id, self.child_node.segment if self.child_node else None
            )
        }
