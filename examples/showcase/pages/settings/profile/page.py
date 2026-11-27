"""Profile form. Saving runs a server callback that validates and then calls `navigate(target)`.

`navigate` only sets the browser's location. The router then renders the confirmation page as a
normal navigation (skeletons included), which costs one more roundtrip than rendering it inside
the callback.
"""

import dash_mantine_components as dmc
from dash import Input, Output, State, callback

from dash_router import navigate, url_for
from ui import section


def page(**_):
    return section(
        "Profile",
        dmc.Stack(
            [
                dmc.TextInput(id="profile-name", label="Display name", value="Ada Lovelace"),
                dmc.TextInput(id="profile-email", label="Email", value="ada@northwind.example"),
                dmc.Group([dmc.Button("Save", id="profile-save")], justify="flex-end"),
            ]
        ),
        features=("server callback -> navigate()",),
    )


@callback(
    Output("profile-email", "error"),
    Input("profile-save", "n_clicks"),
    State("profile-name", "value"),
    State("profile-email", "value"),
    running=[(Output("profile-save", "loading"), True, False)],
    prevent_initial_call=True,
)
def save_profile(n_clicks, name, email):
    if not n_clicks:
        return None
    if not email or "@" not in email:
        return "Please enter a valid email address"
    target = url_for("settings/saved", name=name or "")
    navigate(target)
    return None
