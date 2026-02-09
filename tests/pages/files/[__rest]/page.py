import random

from dash import dcc, html

from components import create_box


async def layout(rest: list | None = None, *args, **kwargs):
    link_count = random.randint(1, 5)
    base_path = "/files"
    rest_segments = rest or []
    url = base_path if not rest_segments else f"{base_path}/" + "/".join(rest_segments)
    links = html.Ul(
        [
            html.Li(
                dcc.Link(
                    f"{url}/{index}",
                    href=f"{url}/{index}",
                )
            )
            for index in range(1, link_count + 1)
        ],
        style={"margin": "0"},
    )

    content = html.Div(
        [
            html.H4("Catch-all file links", style={"marginBottom": "4px"}),
            html.P(
                f"Generated {link_count} link(s) under {url}.",
                style={"marginTop": "0"},
            ),
            links,
        ]
    )

    return create_box(
        "tests/pages/files/[__rest]/page.py",
        content,
        rest=rest,
        *args,
        **kwargs,
    )
