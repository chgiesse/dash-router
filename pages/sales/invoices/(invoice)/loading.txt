import dash_mantine_components as dmc
from dash import dcc

layout = dmc.Center(
    dcc.Loading(
        custom_spinner=dmc.Loader(type="dots").to_plotly_json(),
        delay_show=200,
        show_initially=False,
        display="show",
    ),
    m="md",
)
