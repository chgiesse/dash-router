import json

from dash import _dash_renderer, html
from flash import ALL, Flash, Input, Output, State, callback
from quart import request

from appshell import create_appshell
from router import RootContainer, Router

# from pages.sales.page import layout


_dash_renderer._set_react_version("18.2.0")
app = Flash(__name__, suppress_callback_exceptions=True)

router = Router(app)

app.layout = create_appshell([RootContainer()])

# print(router.route_registry.routes)


@callback(
    Output("dash-router-dummy-container", "children"),
    Input("click", "n_clicks"),
    State(
        {"type": "DASH-ROUTER-SLOT-ROUTE-CONTAINER", "index": ALL},
        "id",
    ),
)
def show_id(_id, ids):
    print("FUCK YOU", ids, flush=True)
    return html.Div(id={"type": "DASH-ROUTER-SLOT-ROUTE-CONTAINER", "index": "test"})
    # return str(_id)


@app.server.before_request
async def test():
    data = await request.get_data()
    if b"click.n_clicks" in data:
        return {
            "multi": True,
            "response": {
                RootContainer.ids.container: {
                    "children": html.Div("test").to_plotly_json()
                },
            },
        }


def recursive_to_plotly_json(component):
    if hasattr(component, "to_plotly_json"):
        component = component.to_plotly_json()
        children = component["props"].get("children")

        if isinstance(children, list):
            component["props"]["children"] = [
                recursive_to_plotly_json(child) for child in children
            ]
        else:
            component["props"]["children"] = recursive_to_plotly_json(children)

    return component


def process_output(view_function, path):
    children = recursive_to_plotly_json(view_function())
    response_data = dict(
        multi=True,
        response={
            RootContainer.ids.container: {"children": children},
        },
    )
    response_data = json.dumps(response_data)
    return response_data


if __name__ == "__main__":
    app.run(debug=True, port=8031)
