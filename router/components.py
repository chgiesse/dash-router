from dash import html, dcc
from dash.development.base_component import Component
import random

class ChildContainer(html.Div):   

    class ids:
        container = lambda segment: {'type': 'DASH-ROUTER-CHILD-ROUTE-CONTAINER', 'index': str(segment) + '-children'}

    def __init__(self, layout: Component, segment: str, *args, **kwargs):

        super().__init__(
            id=self.ids.container(segment),
            children=layout,
            *args,
            **kwargs
        )

class SlotContainer(html.Div):

    class ids:
        container = lambda segment, slot_name: {'type': 'DASH-ROUTER-SLOT-ROUTE-CONTAINER', 'index': str(segment) + '-slot-' + str(slot_name)}

    def __init__(self, layout: Component, segment: str, slot_name: str, *args, **kwargs):

        super().__init__(
            id=self.ids.container(segment, slot_name),
            children=layout,
            *args,
            **kwargs
        )


class RootContainer(html.Div):

    class ids:
        container = 'dash-router-root-container'
        location = 'dash-router-location'
        state_store = 'dash-router-loading-state-store'
        dummy = 'dash-router-dummy-container'
    
    def __init__(self) -> None:
        super().__init__([
            dcc.Location(id=self.ids.location),
            html.Div(id=self.ids.container, disable_n_clicks=True),
            dcc.Store(id=self.ids.state_store, data={}),
            html.Div(id=self.ids.dummy, disable_n_clicks=True)
        ])