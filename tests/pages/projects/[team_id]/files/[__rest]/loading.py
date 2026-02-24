from dash import dcc, html

layout = html.Div(
    dcc.Loading(
        type="circle",
        display="show",
    ),
    style={"margin": "2rem", "height": "5rem"},
)
