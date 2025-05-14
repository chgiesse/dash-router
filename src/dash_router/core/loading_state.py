from dash_router.models import LoadingStateType
from dash_router.core.routing import PageNode

from pydantic import BaseModel
from typing import Dict


class LoadingState(BaseModel):
    value: str | int | float
    state: LoadingStateType


class LoadingStates:
    def __init__(self, init_loading_state: Dict[str, Dict]):
        self._states = {
            nid: LoadingState(**ils) for nid, ils in init_loading_state.items()
        }

    def get_state(self, node: PageNode, value):
        ls = self._states.get(node.node_id)
        if ls:
            return ls.state

    def get_value(self, node: PageNode):
        ls = self._states.get(node.node_id)
        return ls.value

    def update(self, node: PageNode, state, value):
        ls = LoadingState(value=value, state=state)
        self._states[node.node_id] = ls

    def update_state(self, node: PageNode, state: LoadingStateType):
        self._states[node.node_id].state = state
