import random
import asyncio
from dash import dcc, html

from components import create_box


async def layout(
    rest: list | None = None,
    team_id: str | None = None,
    **kwargs,
):
    # Simulate loading for nested paths
    rest_segments = rest or []
    if len(rest_segments) > 0:
        await asyncio.sleep(1.2)

    base_path = f"/projects/{team_id}/files"
    url = base_path if not rest_segments else f"{base_path}/" + "/".join(rest_segments)

    # Breadcrumb
    breadcrumb_items = [html.Span("projects", className="muted")]
    breadcrumb_items.append(html.Span(f"/ {team_id}", className="muted"))
    if rest_segments:
        breadcrumb_items.append(html.Span(f"/ {'/'.join(rest_segments)}", className="muted"))

    # Generate some file/folder cards
    link_count = random.randint(3, 7)
    cards = []
    for i in range(1, link_count + 1):
        name = f"{rest_segments[-1] if rest_segments else 'item'}-{i}.txt"
        # folders for the first two
        is_folder = i <= 2
        target = f"{url}/{name.replace('.txt','') if is_folder else name}"
        thumb_class = "file-thumb folder" if is_folder else "file-thumb"
        cards.append(
            dcc.Link(
                html.Div([
                    html.Div([html.Div(name[0].upper(), className=thumb_class), html.Div([html.Div(name, className="file-name"), html.Div("Size: 2KB", className="file-sub")])], className="file-meta")
                ], className="file-card"),
                href=target,
            )
        )

    file_grid = html.Div(cards, className="file-grid")

    content = html.Div([
        html.Div(breadcrumb_items, className="breadcrumb"),
        html.H4("Files", style={"marginTop": "8px"}),
        html.P(f"Viewing: {url}", className="muted"),
        file_grid,
    ])

    return create_box(
        "tests/pages/projects/[team_id]/files/[__rest]/page.py",
        content,
        rest=rest,
        team_id=team_id,
        **kwargs,
    )
