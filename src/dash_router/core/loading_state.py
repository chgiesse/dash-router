from dash_router.models import LoadingStateType

from pydantic import BaseModel
from typing import Dict, Optional


class LoadingState(BaseModel):
    # value: str | int | float
    state: LoadingStateType
    node_id: str
    updated: bool = False

    def update_state(self, state: LoadingStateType) -> None:
        self.state = state
        self.updated = True


class LoadingStates:
    def __init__(self, init_loading_state: Dict[str, Dict]):
        self._states = {
            segment_key: LoadingState(**ils)
            for segment_key, ils in init_loading_state.items()
        }

    def clear(self) -> None:
        """Clear all loading states"""
        self._states.clear()

    def get_state(self, segment_key: str) -> Optional[LoadingStateType]:
        """Get loading state for a node and segment key"""
        ls = self._states.get(segment_key)
        if ls:
            return ls.state
        return None

    def set_state(
        self, node_id: str, segment_key: str, state: LoadingStateType
    ) -> None:
        """Set loading state for a node and segment key"""
        if segment_key not in self._states:
            self._states[segment_key] = LoadingState(
                state=state, node_id=node_id, updated=True
            )
        else:
            self._states[segment_key].update_state(state)

    def get_node_id(self, segment_key: str) -> Optional[str]:
        """Get node ID for a segment key"""
        ls = self._states.get(segment_key)
        return ls.node_id if ls else None

    def get_all_nodes(self) -> Dict[str, str]:
        """Get all node IDs mapped to their segment keys"""
        return {key: state.node_id for key, state in self._states.items()}

    def to_dict(self) -> Dict[str, Dict]:
        """Convert states to dictionary format"""
        return {
            key: {"state": state.state, "node_id": state.node_id}
            for key, state in self._states.items()
            if state.updated == True
        }
