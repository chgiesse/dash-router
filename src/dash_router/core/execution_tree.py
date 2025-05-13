from typing import List
from .route_node import PageNode


class ExecTree:

    def __init__(
            self, 
            variables, 
            query_params, 
            loading_state, 
            request_pathname, 
            endpoints, 
            is_init
        ) -> None:
        self.variables = variables
        self.query_params = query_params
        self.loading_state = loading_state 
        self.request_pathname = request_pathname
        self.endpoints = endpoints
        self.is_init = is_init


    def build(self, current_node: PageNode, segments: List[str]):
        """Recursively builds the execution tree for the matched route."""
        if not current_node:
            return current_node

    async def execute(self):
        pass    

    def get_loading_state(self):
        pass

    def update_loading_state(self):
        pass

    
