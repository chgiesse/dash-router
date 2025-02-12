from dash import dcc, html
from dash.development.base_component import Component


class ChildContainer(html.Div):
    class ids:
        container = lambda segment: {
            "type": "DASH-ROUTER-CHILD-ROUTE-CONTAINER",
            "index": str(segment) + "-children",
        }

    class props:
        active = None

    def __init__(
        self,
        layout: Component,
        parent_segment: str,
        segment: str = None,
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
        container = lambda segment, slot_name: {
            "type": "DASH-ROUTER-SLOT-ROUTE-CONTAINER",
            "index": str(segment) + "-slot-" + str(slot_name),
        }

    class props:
        active = None
        is_loaded = None

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
        container = "dash-router-root-container"
        location = "dash-router-location"
        state_store = "dash-router-loading-state-store"
        dummy = "dash-router-dummy-container"

    def __init__(self) -> None:
        super().__init__(
            [
                dcc.Location(id=self.ids.location),
                html.Div(id=self.ids.container, disable_n_clicks=True),
                dcc.Store(id=self.ids.state_store, data={}),
                html.Div(id=self.ids.dummy, disable_n_clicks=True),
            ]
        )


class LacyContainer(html.Div):
    class ids:
        container = lambda index: {
            "index": index,
            "type": "dash-router-lacy-component",
        }

    # @callback(
    #     Output(ids.container(MATCH), "children"),
    #     Input(ids.container(MATCH), "id"),
    #     State(RootContainer.ids.location, "pathname"),
    #     State(RootContainer.ids.state_store, "data"),
    # )
    # def load_lacy_compenent(_, path, loading_state):
    #     print("PATH IN LACY: ", path, loading_state, flush=True)
    #     return no_update

    def __init__(self, children: Component, segment: str):
        data_prop = {"data-path": segment}

        super().__init__(
            children, disable_n_clicks=True, id=self.ids.container(segment), **data_prop
        )
