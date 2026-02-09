from flash import callback, Input, Output
from quart.ctx import after_this_request
from dash import html, dcc


def redirect(*args, **kwargs):
    @after_this_request
    def handle_redirect(response):
        print(args, kwargs)
        print(response)
        return response


button = html.Button("Click Me - Check redirect", id="test-redirect-button")
url = dcc.Location(id="test-redirect-location")


@callback(
    Output("test-redirect-location", "href"),
    Input("test-redirect-button", "n_clicks"),
    prevent_inital_call=True,
)
def redirect_callback(_):
    redirect("Test")
    return "/files/1/2"
