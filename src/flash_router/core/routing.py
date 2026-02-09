from ..utils.helper_functions import _parse_path_variables
from ..utils.constants import DEFAULT_LAYOUT_TOKEN, REST_TOKEN

from typing import (
    Any,
    Callable,
    Dict,
    List,
    Awaitable,
    Optional,
    ClassVar,
    Tuple,
)
from dash.development.base_component import Component
from dash._utils import AttributeDict
from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID


class RouteConfig(BaseModel):
    default_child: str | None = None
    is_static: bool | None = None
    title: str | None = None
    description: str | None = None
    name: str | None = None
    order: int | None = None
    image: str | None = None
    image_url: str | None = None
    redirect_from: List[str] | None = None


class RouterResponse(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    response: Dict[str, Any]
    mimetype: str = "application/json"
    multi: bool = False


class PageNode(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)

    segment_value: str = Field(alias="_segment")  # Changed to use alias
    node_id: str
    layout: Callable[..., Awaitable[Component]] | Component
    default_layout: Optional[Callable[..., Awaitable[Component]] | Component] = None
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
    endpoint: Optional[Callable[..., Awaitable[Any]]] = None
    endpoint_inputs: Optional[List[Any]] = None

    @property
    def is_slot(self) -> bool:
        segment = self.segment_value
        return segment.startswith("(") and segment.endswith(")")

    @property
    def is_path_template(self) -> bool:
        segment = self.segment_value
        return segment.startswith("[") and segment.endswith("]")

    @property
    def segment(self) -> str:
        if self.is_path_template:
            return self.segment_value.strip("[]")

        if self.is_slot:
            return self.segment_value.strip("()")

        formatted_segment = self.segment_value.replace("_", "-").replace(" ", "-")
        return formatted_segment

    def register_slot(self, node: "PageNode") -> None:
        if node.segment in self.slots:
            raise KeyError(f"{node.segment} is already registered as slot!")

        self.slots[node.segment] = node.node_id

    def register_route(self, node: "PageNode") -> None:
        if node.segment in self.slots:
            raise KeyError(f"{node.segment} is already registered as parallel route!")

        self.child_nodes[node.segment] = node.node_id

    def register_path_template(self, node: "PageNode") -> None:
        if self.path_template:
            raise ValueError(f"{node.segment} already has a path template!")

        self.path_template = node.node_id

    def create_segment_key(self, var):
        if not self.is_path_template:
            return self.segment_value

        path_key = self.segment_value
        path_var = var or DEFAULT_LAYOUT_TOKEN
        filled_template = path_key.replace(self.segment, path_var)
        path_template_key = path_key + filled_template
        return path_template_key

    def get_child_node(self, segment: str) -> Optional["PageNode"]:
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
        return {key: RouteTable.get_node(val) for key, val in self.slots.items()}


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


class RouteTree:
    _static_routes: ClassVar[Dict[str, str]] = {}
    _dynamic_routes: ClassVar[AttributeDict] = AttributeDict(
        routes={}, path_template=None
    )

    def __new__(cls):
        raise TypeError("RouteTree is a static class and should not be instantiated")

    @classmethod
    def add_static_route(cls, new_node: PageNode) -> None:
        if new_node.path in cls._static_routes:
            raise KeyError(
                f"{new_node.segment} with path {new_node.path} is already present in static routes"
            )

        cls._static_routes[new_node.path] = new_node

    @classmethod
    def add_root_route(cls, new_node: PageNode) -> None:
        if new_node.is_path_template:
            if cls._dynamic_routes.path_template:
                raise ValueError(f"{new_node.segment} already has a path template!")

            cls._dynamic_routes.path_template = new_node.node_id

        if new_node.segment in cls._dynamic_routes.routes:
            raise KeyError(
                f"{new_node.segment} with path {new_node.path} is already present in static routes"
            )

        cls._dynamic_routes.routes[new_node.segment] = new_node.node_id

    @classmethod
    def get_root_node(cls, ctx) -> Optional[PageNode]:
        missed_segments: str = None
        node: PageNode = None

        for segment in ctx.segments:
            if missed_segments:
                segment = missed_segments + "/" + segment

            if node_id := cls._dynamic_routes.routes.get(segment):
                node = RouteTable.get_node(node_id)
                ctx.segments.pop(0) if ctx.segments else None
                return node

            if node_id := cls._dynamic_routes.path_template:
                node = RouteTable.get_node(node_id)
                ctx.path_vars[node.segment] = segment
                return node

            missed_segments = segment
            ctx.segments.pop(0) if ctx.segments else None

        return node

    @classmethod
    def get_active_root_node(cls, ctx, ignore_empty_folders: bool):
        active_node = cls.get_root_node(ctx)
        ctx.segments = list(reversed(ctx.segments))

        while ctx.segments:
            if active_node is None:
                return active_node

            next_segment = ctx.peek_segment()
            segment_key = active_node.create_segment_key(next_segment)
            segment_loading_state = ctx.get_node_state(segment_key)

            if not segment_loading_state:
                return active_node

            if active_node.is_path_template:
                if len(ctx.segments) <= 1:
                    return active_node

                ctx.consume_path_var(active_node)
                next_segment = ctx.peek_segment()

            ctx.set_node_state(active_node, "done", segment_key)
            ctx.set_silent_loading_states(active_node, "done")

            if child_node := active_node.get_child_node(next_segment):
                if child_node.is_path_template and child_node.segment == REST_TOKEN:
                    return child_node

                if not child_node.is_path_template:
                    ctx.pop_segment()

                active_node = child_node
                continue

            ctx.merge_segments(ignore_empty_folders)

        return active_node

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
    def get_static_route(cls, ctx) -> Tuple[PageNode, Dict[str, Any]]:
        path_variables = {}
        if not ctx.pathname:
            index_node = cls._static_routes.get("/")
            return index_node, path_variables

        for page_path, page_id in cls._static_routes.items():
            if "[" in page_path and "]" in page_path:
                path_variables = _parse_path_variables(ctx.pathname, page_path)
                if path_variables:
                    page_node = RouteTable.get_node(page_id)
                    return page_node, path_variables

            if ctx.pathname == page_path:
                page_node = RouteTable.get_node(page_id)
                return page_node, path_variables

        return None, path_variables
