from hmac import new
from ..utils.helper_functions import _parse_path_variables
from .route_table import route_table
from .route_node import PageNode

from typing import Dict, Tuple


class RouteTree:

    def __init__(self) -> None:
        self._static_routes: Dict[str, str] = {}
        self._dynamic_routes: Dict[str, str] = {}

    
    def add_static_route(self, new_node: PageNode) -> None:
        if new_node.path in self._static_routes:
            raise KeyError(f'{new_node.segment} with path {new_node.path} is already present in static routes')
        
        self._static_routes[new_node.path] = new_node

 
    def add_root_route(self, new_node: PageNode):
        if new_node.segment in self._dynamic_routes:
            raise KeyError(f'{new_node.segment} with path {new_node.path} is already present in static routes')

        self._dynamic_routes[new_node.segment] = new_node


    def add_node(self, new_node: PageNode, parent_node: PageNode | None) -> None:
        if new_node.is_static:
            self.add_static_route(new_node)
            return
        
        if new_node.is_root:
            self.add_root_route(new_node)
            return
        
        if new_node.is_slot:
            parent_node.register_slot(new_node)
            return
        
        if new_node.is_path_template:
            parent_node.register_path_template(new_node)
            return
        
        parent_node.register_route(new_node)


    def get_static_route(self, path: str | None) -> Tuple[PageNode, Dict[str, any]]:
        path_variables = None
        if not path:
            index_node = self._static_routes.get('/')
            return index_node, path_variables

        for page_path, page_id in self._static_routes.items():
            if '[' in page_path and ']' in page_path:
                path_variables = _parse_path_variables(path, page_path)
                if path_variables:
                    page_node = route_table.get_node(page_id)
                    return page_node, path_variables
            
            if path == page_path:
                page_node = route_table.get_node(page_id)
                return page_node, path_variables
        
        return None, path_variables
        

route_tree = RouteTree()
    