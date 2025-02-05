from dash import html


async def layout(**kwargs):
    print(kwargs, " in positions", flush=True)
    return html.Div("All positions")
