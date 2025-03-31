import asyncio
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Awaitable
from uuid import UUID

from dash import html
from dash.development.base_component import Component
from pydantic import BaseModel, Field, ValidationError, field_validator

from ._utils import create_pathtemplate_key
from .components import ChildContainer, LacyContainer, SlotContainer


class RouteConfig(BaseModel):
    path_template: str | None = None
    default_child: str | None = None
    is_static: bool = False
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
    node_id: UUID
    layout: Callable[..., Awaitable[Component]] | Component
    module: str
    segment: str
    parent_segment: str
    path: str | None = None
    path_template: str | None = None
    is_slot: bool = False
    is_static: bool = False
    is_root: bool | None = None
    child_nodes: Dict[str, UUID] = Field(default_factory=dict)
    default_child: str | None = None
    slots: Dict[str, UUID] = Field(default_factory=dict)
    loading: Callable[..., Awaitable[Component]] | Component | None = None
    error: Callable[..., Awaitable[Component]] | Component | None = None
    endpoint: Callable[..., Awaitable[any]] | None = None

    class Config:
        arbitrary_types_allowed = True

    def register_slot(self, node: "PageNode"):
        if node.segment in self.slots:
            raise KeyError(f"{node.segment} is already registered as slot!")

        self.slots[node.segment] = node.node_id

    def register_route(self, node: "PageNode"):
        if node.segment in self.slots:
            raise KeyError(f"{node.segment} is already registered as parallel route!!")

        self.child_nodes[node.segment] = node.node_id

    def get_child_node(self, segment: str, route_table: Dict[UUID, "PageNode"]):
        # Try to match a parallel child first
        if child_id := self.child_nodes.get(segment):
            return route_table.get(child_id)
        # Otherwise, check the slots for a node with a path template
        for slot_id in self.slots.values():
            slot_node = route_table.get(slot_id)
            if slot_node and slot_node.path_template:
                return slot_node
        return None

    def load_config(self, config: RouteConfig):
        config = config or RouteConfig()

        self.path_template = config.path_template
        # self.title = config.title
        # self.description = config.description
        # self.order = config.order
        # self.image = config.image
        # self.image_url = config.image_url
        # self.redirect_from = config.redirect_from
        # self.has_slots = config.has_slots
        self.default_child = config.default_child


class RootNode(BaseModel):
    routes: Dict[str, PageNode] = Field(default_factory=OrderedDict)
    segment: str = "/"

    class Config:
        arbitrary_types_allowed = True

    def register_root_route(self, node: PageNode):
        if node.path in self.routes:
            raise ValueError(f"{node.path} is already registered")

        self.routes[node.path] = node

    def get_route(self, path: str) -> PageNode:
        return self.routes.get(path, None)


@dataclass
class ExecNode:
    """Represents a node in the execution tree"""

    layout: Callable[..., Awaitable[Component]] | Component
    segment: str  # Added to keep track of the current segment
    node_id: UUID
    parent_segment: str
    loading_state: Dict[str, bool]
    path: str
    is_slot: bool = False,
    variables: Dict[str, str] = field(default_factory=dict)
    slots: Dict[str, "ExecNode"] = field(default_factory=dict)
    child_node: Dict[str, "ExecNode"] = field(default_factory=dict)
    path_template: str | None = None
    loading: Callable | Component | None = None
    error: Callable | Component | None = None

    async def execute(
        self, endpoints: Dict[UUID, Dict[any, any]], is_init: bool = True
    ) -> Component:
        """
        Executes the node by rendering its layout with the provided variables,
        slots, and views.
        """
        segment_key = self.segment

        if self.path_template:
            path_key = self.path_template.strip("<>")
            path_variable = self.variables.get(path_key) or 'test' if self.is_slot else None
            segment_key = create_pathtemplate_key(
                self.segment, self.path_template, path_variable, path_key
            )

        segment_loading_state = self.loading_state.get(segment_key, False)
        data = endpoints.get(self.node_id)
        
        if self.loading is not None:
            if is_init and not segment_loading_state:
                self.loading_state[segment_key] = True

                if callable(self.loading):
                    loading_layout = await self.loading()
                else:
                    loading_layout = self.loading

                return LacyContainer(loading_layout, str(self.node_id), self.variables)

        if data is not None and isinstance(data, Exception):
            return await self.handle_error(data, self.variables)

        slots_content, views_content = await asyncio.gather(
            self._handle_slots(is_init, endpoints),
            self._handle_child(is_init, endpoints),
        )
        
        self.loading_state[segment_key] = True
        if callable(self.layout):
            try:
                layout = await self.layout(
                    **self.variables,
                    **slots_content,
                    **views_content,
                    data=data
                )
            except Exception as e:
                layout = await self.handle_error(e, self.variables)
            return layout

        return self.layout
    
    async def handle_error(self, error: Exception, variables: Dict[str, any]):
        if self.error:
            if callable(self.error):
                layout = await self.error(
                    error,
                    variables,
                )
                return layout
            return self.error
        return html.Div(str(error), className="banner")

    async def _handle_slots(
            self, 
            is_init: bool, 
            endpoints: Dict[UUID, Dict[any, any]]
        ) -> Dict[str, Component]:
        """Executes all slot nodes and gathers their rendered components."""
        if self.slots:
            executables = [slot.execute(endpoints, is_init) for slot in self.slots.values()]
            views = await asyncio.gather(*executables)
            results = {}

            for slot_name, slot_layout in zip(self.slots.keys(), views):
                clean_slot_name = slot_name.strip("()")
                results[clean_slot_name] = SlotContainer(
                    slot_layout, self.segment, slot_name
                )

            return results

        return {}

    async def _handle_child(
        self, 
        is_init: bool, 
        endpoints: Dict[UUID, Dict[any, any]]
    ) -> Dict[str, Component]:
        """Executes the current view node."""
        if self.child_node:
            _, child_node = next(iter(self.child_node.items()))
            layout = await child_node.execute(endpoints, is_init) if child_node else None
            return {
                "children": ChildContainer(
                    layout, self.segment, child_node.segment if child_node else None
                )
            }

        return {}


@dataclass
class SyncExecNode:
    """Represents a node in the execution tree"""
    layout: Callable[..., Component] | Component
    segment: str
    node_id: UUID
    parent_segment: str
    loading_state: Dict[str, bool]
    path: str
    variables: Dict[str, str] = field(default_factory=dict)
    slots: Dict[str, "ExecNode"] = field(default_factory=dict)
    child_node: Dict[str, "ExecNode"] = field(default_factory=dict)
    path_template: str | None = None
    loading: Callable | Component | None = None
    error: Callable | Component | None = None

    def execute(self, is_init: bool = True) -> Component:
        """
        Executes the node by rendering its layout with the provided variables,
        slots, and views.
        """
        segment_key = self.segment

        if self.path_template:
            path_key = self.path_template.strip("<>")
            path_variable = self.variables.get(path_key)
            segment_key = create_pathtemplate_key(
                self.segment, self.path_template, path_variable, path_key
            )

        segment_loading_state = self.loading_state.get(segment_key, False)
        if self.loading is not None:
            if is_init and not segment_loading_state:
                self.loading_state[segment_key] = True
                if callable(self.loading):
                    loading_layout = self.loading()
                else:
                    loading_layout = self.loading

                return LacyContainer(loading_layout, str(self.node_id), self.variables)

        views_content = self._handle_child()
        slots_content = self._handle_slots()

        self.loading_state[segment_key] = True
        if callable(self.layout):
            try:
                layout = self.layout(**self.variables, **slots_content, **views_content)
            except Exception as e:
                layout = self.handle_error(e, self.variables)
            return layout

        return self.layout

    def handle_error(self, error: Exception, variables: Dict[str, any]):
        if self.error:
            if callable(self.error):
                layout = self.error(
                    error,
                    variables,
                )
                return layout
            return self.error
        return html.Div(str(error), className="banner")

    def _handle_slots(self) -> Dict[str, Component]:
        """
        Executes all slot nodes and gathers their rendered components.
        """
        if self.slots:
            views = [slot.execute() for slot in self.slots.values()]
            results = {}

            for slot_name, slot_layout in zip(self.slots.keys(), views):
                clean_slot_name = slot_name.strip("()")
                results[clean_slot_name] = SlotContainer(
                    slot_layout, self.segment, slot_name
                )

            return results

        return {}

    def _handle_child(self) -> Dict[str, Component]:
        """
        Executes the current view node.
        """
        if self.child_node:
            _, child_node = next(iter(self.child_node.items()))
            layout = child_node.execute() if child_node else None
            return {
                "children": ChildContainer(
                    layout, self.segment, child_node.segment if child_node else None
                )
            }

        return {}


class RouterResponse(BaseModel):
    response: Dict[str, any]
    mimetype: str = "application/json"
    multi: bool = False

    class Config:
        arbitrary_types_allowed = True
