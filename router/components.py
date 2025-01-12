from dash import html, dcc
from dash.development.base_component import Component
import random

class ChildPageContainer(html.Div):   

    class ids:
        container = lambda segment: {'type': 'DASH-ROUTER-SUB-ROUTE-CONTAINER', 'index': str(segment) + '-children'}

    def __init__(self, layout: Component, segment: str, *args, **kwargs):

        super().__init__(
            id=self.ids.container(segment),
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