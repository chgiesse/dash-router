from typing import Dict
from ..models import LoadingStateType

from pydantic import BaseModel
from dataclasses import dataclass


class LoadingState(BaseModel):
    value: str | int | float
    state: LoadingStateType


class LoadingStates:
    def __init__(self, init_loading_state: Dict[str, Dict]):
        self._states = {nid: LoadingState(**ils) for nid, ils in init_loading_state.items()} 
    
    def get_ls(self, node):
        pass

    def update_ls(self, node):
        pass