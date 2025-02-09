from dash_iconify import DashIconify


def get_icon(icon: str, height: int = 20, *args, **kwargs):
    return DashIconify(icon=icon, height=height, *args, **kwargs)
