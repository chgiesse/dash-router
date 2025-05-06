from .route_node import PageNode

from typing import Dict
from uuid import UUID

class RouteTable:

    def __init__(self) -> None:
        self.table: Dict[UUID, PageNode] = {}

    def add_node(self, node: PageNode) -> None:
        if node.node_id in self.table:
            raise KeyError(f"{node.segment} is already registered!")
        self.table[node.node_id] = node

    def get_node(self, node_id: UUID) -> PageNode:
        return self.table.get(node_id)

route_table = RouteTable()