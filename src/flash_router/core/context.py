import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import partial
from typing import Any, Literal, Optional
from uuid import UUID

from ..utils.constants import DEFAULT_LAYOUT_TOKEN, REST_TOKEN
from .routing import PageNode, RouteTable
from pydantic import BaseModel


class LoadingState(BaseModel):
    state: Literal["lacy", "done", "hidden"]
    node_id: str
    updated: bool = False

    def update_state(self, state: Literal["lacy", "done", "hidden"]) -> None:
        self.state = state
        self.updated = True


@dataclass
class RoutingContext:
    """Encapsulates all routing state for a single request"""

    pathname: str
    query_params: dict[str, Any]
    resolve_type: Literal["search", "url", "lacy"]
    path_vars: dict[str, str] = field(default_factory=dict)
    endpoints: dict[UUID, Callable] = field(default_factory=dict)
    segments: list[str] = field(default_factory=list)
    _loading_states: dict[str, Any] = field(default_factory=dict, repr=False)

    @property
    def variables(self):
        return {**self.query_params, **self.path_vars}

    @classmethod
    def from_request(
        cls,
        pathname: str,
        query_params: dict[str, Any],
        loading_state_dict: dict[str, dict],
        resolve_type: Literal["search", "url", "lacy"],
    ) -> "RoutingContext":
        """Create context from request data"""
        path = pathname.strip("/")
        segments = [seg for seg in path.split("/") if seg] if path else []
        # Build _loading_states dict
        _loading_states = {
            segment_key: LoadingState(**ils)
            for segment_key, ils in loading_state_dict.items()
        }
        return cls(
            pathname=pathname,
            query_params=query_params,
            segments=segments,
            resolve_type=resolve_type,
            _loading_states=_loading_states,
        )

    def get_node_state(self, segment_key: Optional[str] = None) -> Optional[str]:
        """Get loading state for a node"""
        ls = self._loading_states.get(segment_key)
        if ls:
            return ls.state
        return None

    def set_node_state(
        self, node: PageNode, state: str, segment_key: Optional[str] = None
    ):
        """Set loading state for a node"""
        if segment_key not in self._loading_states:
            self._loading_states[segment_key] = LoadingState(
                state=state, node_id=node.node_id, updated=True
            )
        else:
            self._loading_states[segment_key].update_state(state)

    def add_endpoint(self, node: PageNode):
        partial_endpoint = partial(node.endpoint, **self.variables)
        self.endpoints[node.node_id] = partial_endpoint

    def should_lazy_load(
        self, node: PageNode, segment_key: Optional[str] = None
    ) -> bool:
        """Check if node should be lazy loaded"""
        return (
            node.loading is not None
            and self.resolve_type != "lacy"
            and DEFAULT_LAYOUT_TOKEN not in segment_key
        )

    def pop_segment(self) -> Optional[str]:
        """Remove and return the last segment"""
        return self.segments.pop() if self.segments else None

    def peek_segment(self) -> Optional[str]:
        """Peek at the last segment without removing"""
        return self.segments[-1] if self.segments else None

    def consume_path_var(self, node: PageNode) -> Optional[str]:
        """Consume a segment as path variable"""
        if not node.is_path_template:
            return None

        if node.segment == REST_TOKEN:
            rest_value = list(reversed(self.segments))
            self.segments = []
            self.path_vars["rest"] = rest_value
            return rest_value
        else:
            value = self.pop_segment()
            if value:
                self.path_vars[node.segment] = value
            return value

    def merge_segments(self, ignore_empty_folders: bool):
        """Merge segments if empty folder should be ignored"""
        if not ignore_empty_folders or len(self.segments) < 2:
            self.pop_segment()
            return

        first = self.segments.pop()
        second = self.segments.pop()
        combined = f"{first}/{second}"
        self.segments.append(combined)

    async def gather_endpoints(self):
        if not self.endpoints:
            return {}

        keys = list(self.endpoints.keys())
        funcs = list(self.endpoints.values())
        results = await asyncio.gather(
            *[func() for func in funcs], return_exceptions=True
        )
        return dict(zip(keys, results))

    def to_loading_state_dict(self) -> dict[str, Any]:
        """Convert context back to loading state dict for response"""
        return {**self.get_updated_loading_state(), "query_params": self.query_params}

    def get_updated_loading_state(self) -> dict[str, dict]:
        """Return only updated loading states as a dict."""
        return {
            key: {"state": state.state, "node_id": state.node_id}
            for key, state in self._loading_states.items()
            if state.updated == True
        }

    def set_silent_loading_states(self, node: PageNode, state: str = "done"):
        """Mark all descendant slots as done"""
        for slot_name, slot_id in node.slots.items():
            slot_node = RouteTable.get_node(slot_id)
            if slot_node:
                self.set_node_state(slot_node, state, slot_name)
                self.set_silent_loading_states(slot_node, state)
