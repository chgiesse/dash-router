from dash_router.models import LoadingStateType
from dash_router.utils.constants import REST_TOKEN
from ..utils.helper_functions import _parse_path_variables
from .route_table import RouteTable
from .route_node import PageNode

from dash._utils import AttributeDict
from typing import Dict, Tuple, List, ClassVar


class RouteTree:

    _static_routes: ClassVar[Dict[str, str]] = {}
    _dynamic_routes: ClassVar[AttributeDict] = AttributeDict(
        routes={}, 
        path_template=None
    )

    def __new__(cls):
        raise TypeError("RouteTree is a static class and should not be instantiated") 

    @classmethod
    def add_static_route(cls, new_node: PageNode) -> None:
        if new_node.path in cls._static_routes:
            raise KeyError(f'{new_node.segment} with path {new_node.path} is already present in static routes')
        
        cls._static_routes[new_node.path] = new_node

    @classmethod
    def add_root_route(cls, new_node: PageNode) -> None:
        if new_node.is_path_template:
            if cls._dynamic_routes.path_template:
                raise ValueError(f"{new_node.segment} already has a path template!")

            cls._dynamic_routes.path_template = new_node.node_id

        if new_node.segment in cls._dynamic_routes.routes:
            raise KeyError(f'{new_node.segment} with path {new_node.path} is already present in static routes')
        
        cls._dynamic_routes.routes[new_node.segment] = new_node.node_id

    @classmethod
    def get_root_node(cls, segments: List[str]) -> Tuple[PageNode, List, Dict]:
        missed_segments: str = None
        node: PageNode = None
        path_variables: Dict = {}

        for segment in segments:
            if missed_segments:
                segment = missed_segments + '/' + segment

            if node_id := cls._dynamic_routes.routes.get(segment):
                node = RouteTable.get_node(node_id)
                segments = segments[1:]
                return node, segments, path_variables

            if node_id := cls._dynamic_routes.path_template:
                node = RouteTable.get_node(node_id)
                path_variables[node.segment] = segment
                return node, segments, path_variables
            
            missed_segments = segment
            segments = segments[1:]
        
        remaining_segments = segments
        return node, remaining_segments, path_variables
    
    @classmethod
    def get_active_root_node(cls, segments: List[str], loading_state: LoadingStateType, ignore_empty_folders: bool):
        active_node, remaining_segments, variables = cls.get_root_node(segments)
        remaining_segments = list(reversed(remaining_segments))        
        updated_segments = {}
        
        while remaining_segments:
            
            if active_node is None:
                return active_node, remaining_segments, updated_segments, variables
            
            next_segment = remaining_segments[-1] if remaining_segments else None
            segment_key = active_node.create_segment_key(next_segment)
            segment_loading_state = loading_state.get(segment_key)
            
            if not segment_loading_state or segment_loading_state == 'lacy':
                return active_node, remaining_segments, updated_segments, variables
            
            if active_node.is_path_template:

                if len(remaining_segments) <= 1:
                    return active_node, remaining_segments, updated_segments, variables

                varname = active_node.segment
                if active_node.segment == REST_TOKEN:
                    varname = 'rest'
                    next_segment = remaining_segments
                    remaining_segments = []
                
                variables[varname] = next_segment
                remaining_segments = remaining_segments[:-1]
                next_segment = remaining_segments[-1] if remaining_segments else None
            
            updated_segments[segment_key] = 'done'
            
            if child_node := active_node.get_child_node(next_segment):
                remaining_segments = (
                    remaining_segments[:-1] 
                    if not child_node.is_path_template 
                    else remaining_segments
                )
                active_node = child_node
                continue
            
            if not ignore_empty_folders and len(remaining_segments) > 1:
                first = remaining_segments.pop()
                second = remaining_segments.pop()
                combined = f"{first}/{second}"
                remaining_segments.append(combined)
                continue
            
            remaining_segments.pop()
        
        return active_node, remaining_segments, updated_segments, variables


    @classmethod
    def add_node(cls, new_node: PageNode, parent_node: PageNode | None) -> None:
        if new_node.is_static:
            cls.add_static_route(new_node)
            return
        
        if new_node.is_root:
            cls.add_root_route(new_node)
            return
        
        if new_node.is_slot:
            parent_node.register_slot(new_node)
            return
        
        if new_node.is_path_template:
            parent_node.register_path_template(new_node)
            return
        
        parent_node.register_route(new_node)

    @classmethod
    def get_static_route(cls, path: str | None) -> Tuple[PageNode, Dict[str, any]]:
        path_variables = None
        if not path:
            index_node = cls._static_routes.get('/')
            return index_node, path_variables

        for page_path, page_id in cls._static_routes.items():
            if '[' in page_path and ']' in page_path:
                path_variables = _parse_path_variables(path, page_path)
                if path_variables:
                    page_node = RouteTable.get_node(page_id)
                    return page_node, path_variables
            
            if path == page_path:
                page_node = RouteTable.get_node(page_id)
                return page_node, path_variables
        
        return None, path_variables