import asyncio
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Union

from dash import html
from dash.development.base_component import Component
from pydantic import BaseModel, Field, ValidationError, field_validator

from ._utils import create_pathtemplate_key
from .components import ChildContainer, SlotContainer


class RouteConfig(BaseModel):
    path_template: Optional[str] = None
    view_template: Optional[str] = None
    default_child: Optional[str] = None
    is_static: bool = False
    has_slots: bool = False
    title: Optional[str] = None
    description: Optional[str] = None
    name: Optional[str] = None
    order: Optional[int] = None
    image: Optional[str] = None
    image_url: Optional[str] = None
    redirect_from: Optional[List[str]] = None

    @field_validator("path_template")
    def validate_path_template(cls, value: any) -> Optional[str]:
        if not value:
            return None

        if not isinstance(value, str):
            raise ValidationError(
                f"{type(value)} is not a valid type. Has to be either string or none."
            )

        if value.startswith("<") and value.endswith(">"):
            return value

        raise ValidationError("A path template has to start with < and end with >")

    @field_validator("view_template")
    def validate_view_template(cls, value: any) -> Optional[str]:
        if not value:
            return None

        if not isinstance(value, str):
            raise ValidationError(
                f"{type(value)} is not a valid type. Has to be either string or none."
            )

        if value.startswith("[") and value.endswith("]"):
            return value

        raise ValidationError("A path template has to start with [ and end with ]")


class PageNode(BaseModel):
    layout: Callable | Component
    module: str
    segment: str
    parent_segment: str
    path: str | None = None
    path_template: str | None = None
    view_template: str | None = None
    is_slot: bool = False
    is_static: bool = True
    is_root: bool | None = None
    child_nodes: Dict[str, "PageNode"] = Field(default_factory=dict)
    default_child: str | None = None
    slots: Dict[str, "PageNode"] = Field(default_factory=dict)
    is_loading: Callable | Component | None = None
    on_error: Callable | Component | None = None

    class Config:
        arbitrary_types_allowed = True

    def register_slot(self, node: "PageNode"):
        if node.segment in self.slots:
            raise KeyError(f"{node.segment} is already registered as slot!")

        self.slots[node.segment] = node

    def register_route(self, node: "PageNode"):
        if node.segment in self.slots:
            raise KeyError(f"{node.segment} is already registered as parallel route!!")

        self.child_nodes[node.segment] = node

    def get_child_node(self, segment: str):
        # only parallel routes can be matched directly
        if child_node := self.child_nodes.get(segment):
            return child_node

        # if no parallel route is found, search slots for view or path templates
        for slot_name, slot_node in self.slots.items():
            if slot_node.path_template:
                return slot_node

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
        self.view_template = config.view_template
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

    layout: Union[Callable[..., Component], Component]
    segment: str  # Added to keep track of the current segment
    parent_segment: str
    loading_state: Dict[str, bool]
    variables: Dict[str, str] = field(default_factory=dict)
    slots: Dict[str, "ExecNode"] = field(default_factory=dict)
    child_node: Dict[str, "ExecNode"] = field(default_factory=dict)
    path_template: Optional[str] = None

    async def execute(self) -> Component:
        """
        Executes the node by rendering its layout with the provided variables,
        slots, and views.
        """
        slots_content = await self._handle_slots()
        views_content = await self._handle_views()

        combined_kwargs = {**self.variables, **slots_content, **views_content}
        segment_key = self.segment

        if self.path_template:
            path_key = self.path_template.strip("<>")
            path_variable = self.variables.get(path_key)
            segment_key = create_pathtemplate_key(
                self.segment, self.path_template, path_variable, path_key
            )

        self.loading_state[segment_key] = True
        if callable(self.layout):
            try:
                layout = (
                    await self.layout(**combined_kwargs)
                    if asyncio.iscoroutinefunction(self.layout)
                    else self.layout(**combined_kwargs)
                )

            except Exception as e:
                layout = html.Div(e)

            return layout

        return self.layout

    async def _handle_slots(self) -> Dict[str, Component]:
        """
        Executes all slot nodes and gathers their rendered components.
        """
        if self.slots:
            executables = [slot.execute() for slot in self.slots.values()]
            views = await asyncio.gather(*executables)
            results = {}

            for slot_name, slot_layout in zip(self.slots.keys(), views):
                clean_slot_name = slot_name.strip("()")
                results[clean_slot_name] = SlotContainer(
                    slot_layout, self.segment, slot_name
                )

            return results

        return {}

    async def _handle_views(self) -> Dict[str, Component]:
        """
        Executes the current view node.
        """
        if self.child_node:
            _, child_node = next(iter(self.child_node.items()))
            layout = await child_node.execute() if child_node else None
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
