from flash_router.navigation import url_for, routing_callback, get_current_url
from flash import Flash, State, callback, Input, Output, get_app
from dash import html, dcc
import asyncio


button = html.Button("Click Me - Check redirect", id="test-redirect-button")
url = dcc.Location(id="test-redirect-location", refresh="callback-nav")
second_button = html.Button("Second button", "second-btn")
loader = dcc.Loading(
    id="loader",
    type="circle",
    display="hide",
    delay_show=200,
    fullscreen=True,
    overlay_style={"filter": "blur(2px)"},
    style={ "backgroundColor": "var(--bg-elev)" },
)


@routing_callback(
    Input("test-redirect-button", "n_clicks"),
    running=[(Output("loader", "display"), "show", "hide")],
)
async def redirect_callback(_: int):
    await asyncio.sleep(3)
    current_url = get_current_url()
    url = url_for("projects/[team-id]/files/[--rest]", team_id="alpha", rest=["photos", "folder1"])
    url = current_url.to(url).update_params(test="123", test2="456")
    return url
