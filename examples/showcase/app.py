"""Northwind Ops — a real-world tour of every `dash_router` feature.

Run (from this folder):

    granian --interface asgi --host 127.0.0.1 --port 8060 app:server
"""

import sys
from pathlib import Path

import dash_mantine_components as dmc
from dash import Dash
from quart import Quart

APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from dash_router import DashRouter, RootContainer  # noqa: E402

server = Quart(__name__)

app = Dash(
    __name__,
    server=server,
    use_pages=False,
    suppress_callback_exceptions=True,
    update_title=None,  # type: ignore[arg-type]
    title="Northwind Ops",
)


def not_found(**_: object) -> dmc.Center:
    return dmc.Center(
        dmc.Stack(
            [
                dmc.Title("404 · Nothing here", order=2),
                dmc.Text("No route matches this URL. This is DashRouter's `not_found_layout`.", c="dimmed"),
                dmc.Anchor("Back to the overview", href="/overview"),
            ],
            align="center",
        ),
        h="70vh",
    )


router = DashRouter(app, pages_folder=APP_DIR / "pages", not_found_layout=not_found)

app.layout = dmc.MantineProvider(
    RootContainer(),
    theme={"primaryColor": "indigo", "defaultRadius": "md"},
    forceColorScheme="dark",
)
