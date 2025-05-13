from ..utils.constants import DEFAULT_LAYOUT_TOKEN

from typing import Callable, Dict, List, Awaitable, Optional
from dash.development.base_component import Component
from pydantic import BaseModel, Field, field_validator, ValidationError
from uuid import UUID


class RouteConfig(BaseModel):
    path_template: str | None = None
    default_child: str | None = None
    is_static: bool | None = None
    title: str | None = None
    description: str | None = None
    name: str | None = None
    order: int | None = None
    image: str | None = None
    image_url: str | None = None
    redirect_from: List[str] | None = None

    @field_validator("path_template")
    def validate_path_template(cls, value: any) -> str | None:
        if not value:
            return None

        if not isinstance(value, str):
            raise ValidationError(
                f"{type(value)} is not a valid type. Has to be either string or none."
            )

        if value.startswith("<") and value.endswith(">"):
            return value

        raise ValidationError("A path template has to start with < and end with >")


class PageNode(BaseModel):
    segment_value: str = Field(alias="_segment")  # Changed to use alias
    node_id: str
    layout: Callable[..., Awaitable[Component]] | Component
    module: str
    parent_id: Optional[str] = None
    path: Optional[str] = None
    is_static: bool = False
    is_root: Optional[bool] = None
    default_child: Optional[str] = None
    child_nodes: Dict[str, UUID] = Field(default_factory=dict)
    slots: Dict[str, str] = Field(default_factory=dict)
    path_template: Optional[str] = None 
    loading: Optional[Callable[..., Awaitable[Component]] | Component] = None
    error: Optional[Callable[..., Awaitable[Component]] | Component] = None
    endpoint: Optional[Callable[..., Awaitable[any]]] = None
    endpoint_inputs: Optional[List[any]] = None

    class Config:
        arbitrary_types_allowed = True
        populate_by_name = True  # Allow using either the alias or the attribute name

    @property
    def is_slot(self) -> bool:
        """Check if this node represents a slot."""
        segment = self.segment_value
        return segment.startswith('(') and segment.endswith(')')

    @property
    def is_path_template(self) -> bool:
        """Check if this node represents a path template."""
        segment = self.segment_value
        return segment.startswith('[') and segment.endswith(']')

    @property
    def segment(self) -> str:
        """Get the formatted segment name."""
        if self.is_path_template:
            return self.segment_value.strip('[]')

        if self.is_slot:
            return self.segment_value.strip('()')

        formatted_segment = (
            self.segment_value
            .replace("_", "-")
            .replace(" ", "-")
        )
        return formatted_segment

    def register_slot(self, node: "PageNode") -> None:
        """Register a slot node."""
        if node.segment in self.slots:
            raise KeyError(f"{node.segment} is already registered as slot!")

        self.slots[node.segment] = node.node_id

    def register_route(self, node: "PageNode") -> None:
        """Register a route node."""
        if node.segment in self.slots:
            raise KeyError(f"{node.segment} is already registered as parallel route!")

        self.child_nodes[node.segment] = node.node_id
    
    def register_path_template(self, node: "PageNode") -> None:
        """Register a path template node."""
        if self.path_template:
            raise ValueError(f"{node.segment} already has a path template!")
        
        self.path_template = node.node_id

    def create_segment_key(self, value):
        if not self.is_path_template:
            return self.segment
        
        path_var = value or DEFAULT_LAYOUT_TOKEN
        path_key = self.segment_value
        filled_template = path_key.replace(self.segment, path_var)
        path_template_key = path_key + filled_template
        return path_template_key

    def get_child_node(self, segment: str) -> Optional["PageNode"]:
        """Get a child node by segment."""
        from .route_table import RouteTable  # Import here to avoid circular dependency
        
        if self.default_child and not segment:
            default_node_id = self.child_nodes.get(self.default_child)
            return RouteTable.get_node(default_node_id)
        
        # Try to match a parallel child first
        if child_id := self.child_nodes.get(segment):
            return RouteTable.get_node(child_id)

        # Otherwise, check the slots for a node with a path template
        if self.path_template:
            return RouteTable.get_node(self.path_template)
        
    
    def get_slots(self):
        from .route_table import RouteTable

        return {key: RouteTable.get_node(val) for key, val in self.slots.items()}
        