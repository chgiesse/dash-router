import dash_mantine_components as dmc
from dash import dcc

layout = dcc.Loading(dmc.Loader(type="dots"), delay_show=500)
