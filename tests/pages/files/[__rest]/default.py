from dash import html

from components import create_box


async def layout(rest: list | None = None, **kwargs):
    rest_segments = rest or []
    content = html.Div(
        [
            html.H4("Files index", style={"marginBottom": "4px"}),
            html.P(
                "This is the default view for /files before any segments are provided.",
                style={"marginTop": "0"},
            ),
            html.P(f"Rest segments: {rest_segments}", style={"marginTop": "0"}),
        ]
    )
    return create_box(
        "tests/pages/files/[__rest]/default.py",
        content,
        rest=rest,
        **kwargs,
    )
