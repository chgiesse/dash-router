from .components import ChildPageContainer

from pydantic import BaseModel, Field, field_validator, ValidationError
from dataclasses import dataclass, field
from typing import Optional, Union, Callable, Dict, List
from dash import html
from dash.development.base_component import Component
from collections import OrderedDict

import asyncio


class RouteConfig(BaseModel):
    path_template: Optional[str] = None
    view_template: Optional[str] = None
    has_slots: bool = False
    title: Optional[str] = None
    description: Optional[str] = None
    name: Optional[str] = None
    order: Optional[int] = None
    image: Optional[str] = None
    image_url: Optional[str] = None
    redirect_from: Optional[List[str]] = None

    @field_validator('path_template')
    def validate_path_template(cls, value: any) -> Optional[str]:

        if not value:
            return None
        
        if not isinstance(value, str):
            raise ValidationError(f'{type(value)} is not a valid type. Has to be either string or none.')
        
        if value.startswith('<') and value.endswith('>'):
            return value
        
        raise ValidationError('A path template has to start with < and end with >')
    

    @field_validator('view_template')
    def validate_view_template(cls, value: any) -> Optional[str]:
        if not value:
            return None
        
        if not isinstance(value, str):
            raise ValidationError(f'{type(value)} is not a valid type. Has to be either string or none.')
        
        if value.startswith('[') and value.endswith(']'):
            return value
        
        raise ValidationError('A path template has to start with [ and end with ]')


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
    parallel_routes: Dict[str, 'PageNode'] = Field(default_factory=dict)
    slots: Dict[str, 'PageNode'] = Field(default_factory=dict)
    is_loading: Callable | Component | None = None
    on_error: Callable | Component | None = None

    class Config:
        arbitrary_types_allowed = True


    def register_slot(self, node: 'PageNode'):
        if node.segment in self.slots:
            raise KeyError(f'{node.segment} is already registered as slot!')
    
        self.slots[node.segment] = node


    def register_route(self, node: 'PageNode'):
        if node.segment in self.slots:
            raise KeyError(f'{node.segment} is already registered as parallel route!!')
        
        self.parallel_routes[node.segment] = node


    def get_child_node(self, segment: str):

        if view_node := self.parallel_routes.get(segment):
            return view_node

        if slot_node := self.slots.get(segment):
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


class RootNode(BaseModel):

    routes: Dict[str, PageNode] = Field(default_factory=OrderedDict)
    segment: str = '/'

    class Config:
        arbitrary_types_allowed = True

    def register_root_route(self, node: PageNode):
        if node.path in self.routes:
            raise ValueError(f'{node.path} is already registered')

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
    slots: Dict[str, 'ExecNode'] = field(default_factory=dict)
    views: Dict[str, 'ExecNode'] = field(default_factory=dict)

    async def execute(self) -> Component:
        """
        Executes the node by rendering its layout with the provided variables,
        slots, and views.
        """
        # print('EXECUTE: ', self.segment, self.__dict__)
        slots_content = await self._handle_slots()
        views_content = await self._handle_views()
        # Combine variables, slots, and views into a single dictionary
        combined_kwargs = {**self.variables, **slots_content, **views_content}        
        # If layout is a callable (function), call it with the combined_kwargs
        if callable(self.layout):
            try:
                layout = await self.layout(**combined_kwargs) if asyncio.iscoroutinefunction(self.layout) else self.layout(**combined_kwargs)
                self.loading_state[self.segment] = True

            except Exception as e:
                layout = html.Div(e)

            return layout
        
        # If layout is a Dash Component, return it directly
        return self.layout


    async def _handle_slots(self) -> Dict[str, Component]:
        """
        Executes all slot nodes and gathers their rendered components.
        """
        if self.slots:
            # Create a list of coroutine tasks for all slots
            executables = [slot.execute() for slot in self.slots.values()]
            # Execute all slots concurrently
            results = await asyncio.gather(*executables)
            # Map slot keys to their rendered components
            return dict(zip(self.slots.keys(), results))
        return {}

    async def _handle_views(self) -> Dict[str, Component]:
        """
        Executes all view nodes and gathers their rendered components.
        """
        if self.views:
            # Create a list of coroutine tasks for all views
            view_template, view_node = next(iter(self.views.items()))
            # Execute all views concurrently
            layout = await view_node.execute() if view_node else None
            # Map view keys to their rendered components
            return {view_template: ChildPageContainer(layout, self.parent_segment or self.segment)} 

        return {}
