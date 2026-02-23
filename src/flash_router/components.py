import json
from typing import Any
from collections.abc import Callable
from dash import dcc, html
from dash.development.base_component import Component


ID_Component = Callable[[str], dict[str, str]]
ID_Slot_Component = Callable[[str, str], dict[str, str]]


class ChildContainer(html.Div):
    class ids:
        container: ID_Component = lambda segment: {
            "type": "DASH-ROUTER-CHILD-ROUTE-CONTAINER",
            "index":segment + "-children",
        }

    class props:
        active: str | None = None

    def __init__(
        self,
        layout: Component,
        parent_segment: str,
        segment: str | None = None,
        *args,
        **kwargs,
    ):
        self.props.active = segment

        super().__init__(
            id=self.ids.container(parent_segment),
            children=layout,
            disable_n_clicks=True,
            *args,
            **kwargs,
        )


class SlotContainer(html.Div):
    class ids:
        container: ID_Slot_Component = lambda segment, slot_name: {
            "type": "DASH-ROUTER-SLOT-ROUTE-CONTAINER",
            "index": str(segment) + "-slot-" + str(slot_name),
        }

    class props:
        active: str | None = None
        is_loaded: bool | None = None

    def __init__(
        self,
        layout: Component,
        parent_segment: str,
        slot_name: str,
        is_loaded: bool = True,
        *args,
        **kwargs,
    ):
        self.props.active = parent_segment
        self.props.is_loaded = is_loaded

        super().__init__(
            id=self.ids.container(parent_segment, slot_name),
            children=layout,
            disable_n_clicks=True,
            *args,
            **kwargs,
        )


class RootContainer(html.Div):
    class ids:
        container: str = "dash-router-root-container"
        location: str = "dash-router-location"
        state_store: str = "dash-router-loading-state-store"
        dummy: str = "dash-router-dummy-location"

    def __init__(self) -> None:
        super().__init__(
            [
                dcc.Location(id=self.ids.location, refresh="callback-nav"),
                dcc.Location(id=self.ids.dummy, refresh=False),
                html.Div(id=self.ids.container, disable_n_clicks=True),
                dcc.Store(id=self.ids.state_store, data={}),
            ]
        )


class LacyContainer(html.Div):
    class ids:
        container: ID_Component = lambda index: {
            "index": index,
            "type": "dash-router-lacy-component",
        }

    def __init__(self, children: Component, node_id: str, variables: dict[str, Any]):
        data_prop = {"data-path": json.dumps(variables)}

        super().__init__(
            children, disable_n_clicks=True, id=self.ids.container(node_id), **data_prop
        )
