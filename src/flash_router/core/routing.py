# from flash_router.core.context import RoutingContext
from ..utils.helper_functions import _parse_path_variables
from ..utils.constants import DEFAULT_LAYOUT_TOKEN, REST_TOKEN
from ..types import QueryParams, PathVariables, ResolveType, StateType, Endpoint, Layout, ErrorLayout, EndpointResults

from pydantic import BaseModel, ConfigDict, Field
from typing import Any, ClassVar
from functools import partial
import asyncio


class RouteConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)

    default_child: str | None = None
    is_static: bool | None = None
    title: str | None = None
    description: str | None = None
    name: str | None = None
    order: int | None = None
    image: str | None = None
    image_url: str | None = None
    redirect_from: list[str] | None = None
    default_layout: Layout | None = Field(default=None, alias="default")
    loading: Layout | None = None
    error: ErrorLayout | None = None


class RouterResponse(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    response: dict[str, Any]
    mimetype: str = "application/json"
    multi: bool = False


class PageNode(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)

    segment_value: str = Field(alias="_segment")  # Changed to use alias
    node_id: str
    layout: Layout
    module: str
    path: str
    default_layout: Layout | None = None
    parent_id: str | None = None
    is_static: bool = False
    is_root: bool | None = None
    default_child: str | None = None
    child_nodes: dict[str, str] = Field(default_factory=dict)
    slots: dict[str, str] = Field(default_factory=dict)
    path_template: str | None = None
    loading: Layout | None = None
    error: ErrorLayout | None = None
    endpoint: Endpoint | None = None
    endpoint_inputs: set[str] = Field(default_factory=set)

    @property
    def is_slot(self):
        segment = self.segment_value
        return segment.startswith("(") and segment.endswith(")")

    @property
    def is_path_template(self):
        segment = self.segment_value
        return segment.startswith("[") and segment.endswith("]")

    @property
    def segment(self):
        if self.is_path_template:
            return self.segment_value.strip("[]")

        if self.is_slot:
            return self.segment_value.strip("()")

        formatted_segment = self.segment_value.replace("_", "-").replace(" ", "-")
        return formatted_segment

    def register_slot(self, node: "PageNode"):
        if node.segment in self.slots:
            raise KeyError(f"{node.segment} is already registered as slot!")
        self.slots[node.segment] = node.node_id

    def register_route(self, node: "PageNode"):
        if node.segment in self.slots:
            raise KeyError(f"{node.segment} is already registered as parallel route!")
        self.child_nodes[node.segment] = node.node_id

    def register_path_template(self, node: "PageNode"):
        if self.path_template:
            raise ValueError(f"{node.segment} already has a path template!")
        self.path_template = node.node_id

    def create_segment_key(self, var: str | None):
        if not self.is_path_template:
            return self.segment_value

        path_key = self.segment_value
        path_var = var or DEFAULT_LAYOUT_TOKEN
        filled_template = path_key.replace(self.segment, path_var)
        path_template_key = path_key + filled_template
        return path_template_key

    def get_child_node(self, segment: str | None) -> "PageNode | None":
        """
        Resolve child node with the following priority:
        1. Default child (when no segment provided)
        2. Explicit child match (static routes)
        3. Path template (dynamic routes)

        This ensures /users/settings takes precedence over /users/[id]
        """

        if not segment and self.default_child:
            default_node_id = self.child_nodes.get(self.default_child)
            return RouteRegistry.get_node(default_node_id)

        if child_id := self.child_nodes.get(segment):
            return RouteRegistry.get_node(child_id)

        if self.path_template:
            return RouteRegistry.get_node(self.path_template)

        return None

    def get_slots(self):
        return {key: RouteRegistry.get_node(val) for key, val in self.slots.items()}


class DynamicRootRegistry(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    routes: dict[str, str] = Field(default_factory=dict)
    path_template: str | None = None


class RouteRegistry:
    """Unified registry for all route nodes and root entry points"""

    _nodes: ClassVar[dict[str, PageNode]] = {}
    _static_root: ClassVar[dict[str, PageNode]] = {}
    _dynamic_root: ClassVar[DynamicRootRegistry] = DynamicRootRegistry()

    def __new__(cls):
        raise TypeError("RouteRegistry is a static class and should not be instantiated")

    # --- Node Management ---

    @classmethod
    def add_node(cls, node: PageNode) -> None:
        if node.node_id in cls._nodes:
            raise KeyError(f"{node.segment} is already registered!")
        cls._nodes[node.node_id] = node

    @classmethod
    def get_node(cls, node_id: str | None) -> PageNode | None:
        if node_id is None:
            return None
        return cls._nodes.get(node_id)

    @classmethod
    def register_node(cls, new_node: PageNode, parent_node: PageNode | None) -> None:
        """Register a node in the appropriate root or parent"""
        if new_node.is_static:
            cls._add_static_root(new_node)
            cls.add_node(new_node)
            return

        if new_node.is_root:
            cls._add_dynamic_root(new_node)
            cls.add_node(new_node)
            return

        if parent_node is None:
            raise ValueError(f"Non-root node {new_node.segment} must have a parent node")

        if new_node.is_slot:
            parent_node.register_slot(new_node)
        elif new_node.is_path_template:
            parent_node.register_path_template(new_node)
        else:
            parent_node.register_route(new_node)

        cls.add_node(new_node)

    @classmethod
    def _add_static_root(cls, node: PageNode) -> None:
        if node.path in cls._static_root:
            raise KeyError(
                f"{node.segment} with path {node.path} is already present in static roots"
            )
        cls._static_root[node.path] = node

    @classmethod
    def _add_dynamic_root(cls, node: PageNode) -> None:
        if node.is_path_template:
            if cls._dynamic_root.path_template:
                raise ValueError(f"{node.segment} already has a path template!")
            cls._dynamic_root.path_template = node.node_id

        if node.segment in cls._dynamic_root.routes:
            raise KeyError(
                f"{node.segment} with path {node.path} is already present in dynamic roots"
            )
        cls._dynamic_root.routes[node.segment] = node.node_id

    # --- Route Resolution ---

    @classmethod
    def get_static_route(cls, ctx: "RoutingContext") -> tuple[PageNode | None, PathVariables]:
        path_variables: PathVariables = {}

        if not ctx.pathname:
            index_node = cls._static_root.get("/")
            return index_node, path_variables

        for page_path, page_node in cls._static_root.items():
            if "[" in page_path and "]" in page_path:
                path_variables = _parse_path_variables(ctx.pathname, page_path)
                if path_variables:
                    return page_node, path_variables

            if ctx.pathname == page_path:
                return page_node, path_variables

        return None, path_variables

    @classmethod
    def get_root_node(cls, ctx: "RoutingContext") -> PageNode | None:
        missed_segments: str | None = None
        node: PageNode | None = None

        for segment in ctx.segments:
            if missed_segments:
                segment = missed_segments + "/" + segment

            if node_id := cls._dynamic_root.routes.get(segment):
                node = cls.get_node(node_id)
                ctx.segments.pop(0) if ctx.segments else None
                return node

            if node_id := cls._dynamic_root.path_template:
                node = cls.get_node(node_id)
                ctx.path_vars[node.segment] = segment # pyright: ignore[reportOptionalMemberAccess]
                return node

            missed_segments = segment
            ctx.segments.pop(0) if ctx.segments else None

        return node

    @classmethod
    def get_active_root_node(cls, ctx: "RoutingContext", ignore_empty_folders: bool) -> PageNode | None:
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
                _ = ctx.consume_path_var(active_node)
                next_segment = ctx.peek_segment()

            ctx.set_node_state(active_node, "done", segment_key)
            ctx.set_silent_loading_states(active_node, "done")

            if child_node := active_node.get_child_node(next_segment):
                if child_node.is_path_template and child_node.segment == REST_TOKEN:
                    return child_node

                if not child_node.is_path_template:
                    _ = ctx.pop_segment()

                active_node = child_node
                continue

            ctx.merge_segments(ignore_empty_folders)

        return active_node

    # --- Utility ---

    @classmethod
    def reset(cls) -> None:
        """Reset all registries - useful for testing"""
        cls._nodes.clear()
        cls._static_root.clear()
        cls._dynamic_root = DynamicRootRegistry()


class LoadingState(BaseModel):
    state: StateType
    node_id: str
    updated: bool = False

    def update_state(self, state: StateType) -> None:
        self.state = state
        self.updated = True


class RoutingContext(BaseModel):
    """Encapsulates all routing state for a single request"""
    pathname: str
    query_params: QueryParams
    resolve_type: ResolveType
    path_vars: PathVariables = Field(default_factory=dict)
    endpoints: dict[str, Endpoint] = Field(default_factory=dict)
    segments: list[str] = Field(default_factory=list)
    loading_states: dict[str, LoadingState] = Field(default_factory=dict, repr=False)

    @property
    def variables(self):
        return {**self.query_params, **self.path_vars}

    @classmethod
    def from_request(
        cls,
        pathname: str,
        query_params: QueryParams,
        loading_state_dict: dict[str, PathVariables],
        resolve_type: ResolveType,
    ):
        """Create context from request data"""
        path = pathname.strip("/")
        segments = [seg for seg in path.split("/") if seg] if path else []
        loading_states = {
            segment_key: LoadingState.model_validate(ils)
            for segment_key, ils in loading_state_dict.items()
        }
        return cls(
            pathname=pathname,
            query_params=query_params,
            segments=segments,
            resolve_type=resolve_type,
            loading_states=loading_states,
        )

    def get_node_state(self, segment_key: str):
        """Get loading state for a node"""
        ls = self.loading_states.get(segment_key)
        if ls:
            return ls.state
        return None

    def set_node_state(self, node: PageNode, state: StateType, segment_key: str):
        """Set loading state for a node"""
        if segment_key not in self.loading_states:
            self.loading_states[segment_key] = LoadingState(
                state=state, node_id=node.node_id, updated=True
            )
        else:
            self.loading_states[segment_key].update_state(state)

    def add_endpoint(self, node: PageNode):
        endpoint = node.endpoint
        if endpoint is None:
            raise ValueError(f"Can not add none present endpoint for Node: {node.node_id}")
        partial_endpoint = partial(endpoint, **self.variables)
        self.endpoints[node.node_id] = partial_endpoint

    def should_lazy_load(self, node: PageNode, segment_key: str):
        return (
            node.loading is not None
            and self.resolve_type != "lacy"
            and DEFAULT_LAYOUT_TOKEN not in segment_key
        )

    def pop_segment(self):
        """Remove and return the last segment"""
        return self.segments.pop() if self.segments else None

    def peek_segment(self):
        """Peek at the last segment without removing"""
        return self.segments[-1] if self.segments else None

    def consume_path_var(self, node: PageNode):
        if not node.is_path_template:
            return None

        if node.segment == REST_TOKEN:
            rest_value = list(reversed(self.segments))
            self.segments = []
            self.path_vars["rest"] = rest_value
            return rest_value
        else:
            value = self.pop_segment()
            if value:
                self.path_vars[node.segment] = value
            return value

    def merge_segments(self, ignore_empty_folders: bool):
        """Merge segments if empty folder should be ignored"""
        if not ignore_empty_folders or len(self.segments) < 2:
            _ = self.pop_segment()
            return

        first = self.segments.pop()
        second = self.segments.pop()
        combined = f"{first}/{second}"
        self.segments.append(combined)

    async def gather_endpoints(self) -> EndpointResults:
        if not self.endpoints:
            return {}

        keys = list(self.endpoints.keys())
        funcs = list(self.endpoints.values())
        results = await asyncio.gather(
            *[func() for func in funcs], return_exceptions=True
        )
        return dict(zip(keys, results))

    def to_loading_state_dict(self):
        """Convert context back to loading state dict for response"""
        return {**self.get_updated_loading_state(), "query_params": self.query_params}

    def get_updated_loading_state(self):
        """Return only updated loading states as a dict."""
        return {
            key: {"state": state.state, "node_id": state.node_id}
            for key, state in self.loading_states.items()
            if state.updated == True
        }

    def set_silent_loading_states(self, node: PageNode, state: StateType = "done"):
        """Mark all descendant slots as done"""
        for slot_name, slot_id in node.slots.items():
            slot_node = RouteRegistry.get_node(slot_id)
            if slot_node:
                self.set_node_state(slot_node, state, slot_name)
                self.set_silent_loading_states(slot_node, state)
