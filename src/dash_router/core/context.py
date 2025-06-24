from ast import Call
import asyncio
from dataclasses import dataclass, field
from functools import partial
from typing import Any, Callable, Dict, List, Literal, Optional, Tuple
from uuid import UUID

from .loading_state import LoadingStates, LoadingState
from ..utils.constants import DEFAULT_LAYOUT_TOKEN, REST_TOKEN
from .routing import PageNode, RouteTable


@dataclass
class RoutingContext:
    """Encapsulates all routing state for a single request"""

    pathname: str
    query_params: Dict[str, Any]
    loading_states: LoadingStates
    resolve_type: Literal["search", "url", "lacy"]
    path_vars: Dict[str, str] = field(default_factory=dict)
    endpoints: Dict[UUID, Callable] = field(default_factory=dict)
    is_init: bool = True
    segments: List[str] = field(default_factory=list)

    @property
    def variables(self):
        return {**self.query_params, **self.path_vars}

    @classmethod
    def from_request(
        cls,
        pathname: str,
        query_params: Dict[str, Any],
        loading_state_dict: Dict[str, Dict],
        resolve_type: Literal["search", "url", "lacy"],
        is_init: bool = True,
    ) -> "RoutingContext":
        """Create context from request data"""
        loading_states = LoadingStates(loading_state_dict)
        path = pathname.strip("/")
        segments = [seg for seg in path.split("/") if seg] if path else []

        return cls(
            pathname=pathname,
            query_params=query_params,
            loading_states=loading_states,
            is_init=is_init,
            segments=segments,
            resolve_type=resolve_type
        )

    def get_node_state(self, segment_key: Optional[str] = None) -> Optional[str]:
        """Get loading state for a node"""
        return self.loading_states.get_state(segment_key)

    def set_node_state(
        self, node: PageNode, state: str, segment_key: Optional[str] = None
    ):
        """Set loading state for a node"""
        self.loading_states.set_state(node.node_id, segment_key, state)

    def add_endpoint(self, node: PageNode):
        partial_endpoint = partial(node.endpoint, **self.variables)
        self.endpoints[node.node_id] = partial_endpoint

    def get_node_by_segment_key(self, segment_key: str) -> Optional[PageNode]:
        """Get node by segment key using loading states"""
        node_id = self.loading_states.get_node_id(segment_key)
        if node_id:
            return RouteTable.get_node(node_id)
        return None

    def should_lazy_load(self, node: PageNode, segment_key: Optional[str] = None) -> bool:
        """Check if node should be lazy loaded"""
        return (
            node.loading is not None
            and self.resolve_type == "url"
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
        if ignore_empty_folders or len(self.segments) < 2:
            self.pop_segment()

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

    def to_loading_state_dict(self) -> Dict[str, Any]:
        """Convert context back to loading state dict for response"""
        return {**self.loading_states.to_dict(), "query_params": self.query_params}

    def set_silent_loading_states(self, node: PageNode, state: str = "done"):
        """
        Mark all descendant nodes (children, slots, path templates) as 'done' 
        since they are not part of the current rendering cycle.
        
        This ensures that previously loaded content stays visible while only 
        returning updated states via to_dict().
        """
        for slot_name, slot_id in node.slots.items():
            slot_node = RouteTable.get_node(slot_id)
            if slot_node:
                self.set_node_state(slot_node, state, slot_name)
                self.set_silent_loading_states(slot_node, state)
