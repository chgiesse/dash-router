"""Catch-all: `/docs/a/b/c` renders this page with `rest=["a", "b", "c"]`."""

import dash_mantine_components as dmc

from data import resolve_doc
from ui import code, link, section


def page(rest: list[str], **_):
    crumbs, page = resolve_doc(rest)
    breadcrumbs = dmc.Breadcrumbs([link("Docs", "/docs")] + [link(title, href) for title, href in crumbs])
    if page is None:
        body = dmc.Alert(
            f"No article at /docs/{'/'.join(rest)}. The catch-all still matched — handling unknown paths is up to the page.",
            color="orange",
            variant="light",
        )
        title = "Article not found"
    else:
        title = str(page.get("_title"))
        children = [(k, v) for k, v in page.items() if not k.startswith("_") and isinstance(v, dict)]
        body = dmc.Stack(
            [
                dmc.Text(str(page.get("_body")), size="sm"),
                dmc.Stack([link(str(v.get("_title", k)), f"/docs/{'/'.join(rest)}/{k}", size="sm") for k, v in children], gap=4)
                if children
                else dmc.Text("No sub-articles.", size="xs", c="dimmed"),
            ]
        )
    return section(
        title,
        dmc.Stack([breadcrumbs, body, dmc.Text(["rest = ", code(repr(rest))], size="xs", c="dimmed")]),
        features=("[__rest]/page.py",),
    )
