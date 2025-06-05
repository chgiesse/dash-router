from dash_router.models import LoadingStateType
from dash_router.core.routing import PageNode

from pydantic import BaseModel
from typing import Dict


class LoadingState(BaseModel):
    # value: str | int | float
    state: LoadingStateType
    node_id: str

    def update_state(self, state: LoadingStateType) -> None:
        self.state = state


class LoadingStates:
    def __init__(self, init_loading_state: Dict[str, Dict]):
        self._states = {
            segment_key: LoadingState(**ils) for segment_key, ils in init_loading_state.items()
        }

    def get_state_obj(self, node: PageNode, segment_key: str):
        ls = self._states.get(segment_key)
        if ls:
            return ls.state

        if node:
            new_loading_state = LoadingState(state=None, node_id=node.node_id)
            self._states[segment_key] = new_loading_state
            return new_loading_state
    
    