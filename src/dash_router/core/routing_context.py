from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple
from uuid import UUID

from .loading_state import LoadingStates, LoadingState
from ..utils.constants import DEFAULT_LAYOUT_TOKEN, REST_TOKEN
from .routing import PageNode


@dataclass
class RoutingContext:
    """Encapsulates all routing state for a single request"""
    pathname: str
    query_params: Dict[str, Any]
    loading_states: LoadingStates
    path_vars: Dict[str, str] = field(default_factory=dict)
    endpoints: Dict[UUID, Callable] = field(default_factory=dict)
    is_init: bool = True
    _segments: List[str] = field(default_factory=list)
    
    @classmethod
    def from_request(cls, pathname: str, query_params: Dict[str, Any], 
                     loading_state_dict: Dict[str, Dict], is_init: bool = True) -> "RoutingContext":
        """Create context from request data"""
        # Remove query_params from loading state dict
        loading_state_dict = loading_state_dict.copy()
        loading_state_dict.pop("query_params", None)
        
        # Create LoadingStates object
        loading_states = LoadingStates(loading_state_dict)
        
        # Parse segments
        path = pathname.strip("/")
        segments = [seg for seg in path.split("/") if seg] if path else []
        
        return cls(
            pathname=pathname,
            query_params=query_params,
            loading_states=loading_states,
            is_init=is_init,
            _segments=segments
        )
    
    def get_node_state(self, node: PageNode, var: Optional[str] = None) -> Optional[str]:
        """Get loading state for a node"""
        segment_key = node.create_segment_key(var)
        return self.loading_states.get_state(node, segment_key)
    
    def set_node_state(self, node: PageNode, state: str, var: Optional[str] = None):
        """Set loading state for a node"""
        segment_key = node.create_segment_key(var)
        self.loading_states.set_state(node, segment_key, state)
    
    def get_node_by_segment_key(self, segment_key: str) -> Optional[PageNode]:
        """Get node by segment key using loading states"""
        node_id = self.loading_states.get_node_id(segment_key)
        if node_id:
            from .routing import RouteTable
            return RouteTable.get_node(node_id)
        return None
    
    def should_lazy_load(self, node: PageNode, var: Optional[str] = None) -> bool:
        """Check if node should be lazy loaded"""
        state = self.get_node_state(node, var)
        segment_key = node.create_segment_key(var)
        return (
            state != "lacy" and 
            node.loading is not None and 
            self.is_init and
            DEFAULT_LAYOUT_TOKEN not in segment_key
        )
    
    def pop_segment(self) -> Optional[str]:
        """Remove and return the last segment"""
        return self._segments.pop() if self._segments else None
    
    def peek_segment(self) -> Optional[str]:
        """Peek at the last segment without removing"""
        return self._segments[-1] if self._segments else None
    
    def consume_path_var(self, node: PageNode) -> Optional[str]:
        """Consume a segment as path variable"""
        if not node.is_path_template:
            return None
            
        if node.segment == REST_TOKEN:
            rest_value = list(reversed(self._segments))
            self._segments = []
            self.path_vars["rest"] = rest_value
            return rest_value
        else:
            value = self.pop_segment()
            if value:
                self.path_vars[node.segment] = value
            return value
    
    def to_loading_state_dict(self) -> Dict[str, Any]:
        """Convert context back to loading state dict for response"""
        return {
            **self.loading_states.to_dict(),
            "query_params": self.query_params
        } 