from .route_node import PageNode

from typing import Dict, ClassVar

class RouteTable:

    _table: ClassVar[Dict[str, PageNode]] = {}
    
    def __new__(cls):
        raise TypeError("RouteTable is a static class and should not be instantiated") 

    @classmethod
    def add_node(cls, node: PageNode) -> None:
        if node.node_id in cls._table:
            raise KeyError(f"{node.segment} is already registered!")
        
        cls._table[node.node_id] = node

    @classmethod
    def get_node(cls, node_id: str) -> PageNode:
        return cls._table.get(node_id)