from flash import callback, Input, Output
from quart.ctx import after_this_request
from quart import Response
from dash import html, dcc
import asyncio
import json


def redirect(*args, **kwargs):
    @after_this_request
    async def handle_redirect(response: Response):
        response_data = await response.get_json()
        await asyncio.sleep(3)
        new_data = {"test-redirect-location": {"href": args[0]}}
        response_data["response"] = new_data
        response.set_data(json.dumps(response_data))
        print("Executed After reuest", response_data, flush=True)
        return response


button = html.Button("Click Me - Check redirect", id="test-redirect-button")
url = dcc.Location(id="test-redirect-location", refresh="callback-nav")
second_button = html.Button("Second button", "second-btn")
loader = dcc.Loading(id="loader", type="circle")


@callback(
    Output("test-redirect-location", "href"),
    Input("test-redirect-button", "n_clicks"),
    running=[(Output("loader", "display"), "show", "hide")],
    prevent_initial_call=True,
)
async def redirect_callback(click):
    print("Executed 1 callback", flush=True)
    redirect(f"/projects/alpha/files/photos/{click}")


@callback(Input("second-btn", "n_clicks"))
async def test2(_):
    print("Executed second callback", flush=True)
