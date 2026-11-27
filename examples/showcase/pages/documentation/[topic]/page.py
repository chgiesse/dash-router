"""One documentation page. `[topic]` is omitted at `/documentation`, which renders the overview.

No `api.py` / `loading.py`: the layout renders on every visit, so the "rendered" badge changes each time.
"""

import dash_mantine_components as dmc
from dash import dcc

from docs_site import DOC_PAGES, doc_href, load_doc, page_by_slug, rewrite_links
from ui import feature_tags, rendered_badge


def _pager(index: int) -> dmc.Group:
    prev_page = DOC_PAGES[index - 1] if index > 0 else None
    next_page = DOC_PAGES[index + 1] if index + 1 < len(DOC_PAGES) else None
    return dmc.Group(
        [
            dmc.Anchor(f"← {prev_page.title}", href=doc_href(prev_page.slug), size="sm") if prev_page else dmc.Box(),
            dmc.Anchor(f"{next_page.title} →", href=doc_href(next_page.slug), size="sm") if next_page else dmc.Box(),
        ],
        justify="space-between",
        mt="xl",
    )


def page(topic: str | None = None, **_):
    slug = "index" if topic is None else topic
    page = page_by_slug(slug)
    if page is None:
        return dmc.Stack(
            [
                dmc.Alert(f'No documentation page called "{topic}".', title="Unknown page", color="red"),
                dmc.Anchor("Back to the documentation overview", href="/documentation", size="sm"),
            ]
        )

    index = DOC_PAGES.index(page)
    text = load_doc(slug)
    if text is None:
        body = dmc.Alert("This page has not been written yet.", title=page.title, color="yellow")
    else:
        body = dmc.Typography(dcc.Markdown(rewrite_links(text), className="docs-markdown", link_target="_self"))

    return dmc.Stack(
        [
            dmc.Group(
                [
                    dmc.Stack(
                        [
                            dmc.Text(f"docs/{slug}.md", size="xs", c="dimmed", ff="monospace"),
                            feature_tags("[topic] omitted = overview", "no api.py / loading.py"),
                        ],
                        gap=4,
                    ),
                    rendered_badge(),
                ],
                justify="space-between",
                align="flex-start",
            ),
            body,
            _pager(index),
        ]
    )
