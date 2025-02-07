from dash import Dash, Input, Output, State  # , _dash_renderer

# from flash import Flash
from appshell import create_appshell
from router import RootContainer, Router

# from pages.sales.page import layout


# _dash_renderer._set_react_version("18.2.0")
# app = Flash(__name__, suppress_callback_exceptions=True)
app = Dash(__name__)
router = Router(app)

app.layout = create_appshell([RootContainer()])

inputs = {
    "pathname_": Input(RootContainer.ids.location, "pathname"),
    "search_": Input(RootContainer.ids.location, "search"),
    "loading_state_": State(RootContainer.ids.state_store, "data"),
}

inputs.update(app.routing_callback_inputs)


@app.callback(Output(RootContainer.ids.dummy, "children"), inputs=inputs)
def update(pathname_: str, search_: str, loading_state_: str, **states):
    return


if __name__ == "__main__":
    app.run(debug=False, port=8031)
