from pprint import pformat

from dash import html


def _format_value(value):
    if isinstance(value, (str, int, float, bool, type(None))):
        return value
    if isinstance(value, (list, tuple)):
        return [_format_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _format_value(item) for key, item in value.items()}
    return f"<{type(value).__name__}>"


def create_box(name: str, content=None, *args, **kwargs):
    formatted_args = [_format_value(item) for item in args]
    formatted_kwargs = {key: _format_value(item) for key, item in kwargs.items()}
    details = pformat({"args": formatted_args, "kwargs": formatted_kwargs}, width=80)
    return html.Div(
        [
            html.Div(name, style={"fontWeight": "600"}),
            html.Pre(details),
            content,
        ],
        style={
            "border": "1px solid #999",
            "padding": "8px",
            "margin": "8px",
        },
    )
