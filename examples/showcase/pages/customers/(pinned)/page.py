import dash_mantine_components as dmc
from dash import html

from dash_router import ChildContainer
from ui import feature_tags


def page(children: ChildContainer, **_):
    hint = dmc.Text(
        "Nothing pinned here. With no default.py, this slot renders empty when the URL doesn't match: "
        "no retention, on soft navigation or hard reload.",
        size="sm",
        c="dimmed",
        className="slot-hint",
    )
    return dmc.Card(
        [
            dmc.Group([dmc.Text("Pinned", fw=600), feature_tags("(pinned): no default.py", "no retention")], justify="space-between", mb="xs"),
            html.Div([children, hint], className="slot-children"),
        ],
        withBorder=True,
        mih=180,
    )
