"""The `docs/` Markdown of `dash_router`, rendered inside the showcase at `/documentation`."""

import re
from dataclasses import dataclass
from pathlib import Path

DOCS_DIR = Path(__file__).resolve().parents[2] / "docs"


@dataclass(frozen=True)
class DocPage:
    slug: str
    title: str


DOC_PAGES: tuple[DocPage, ...] = (
    DocPage("index", "Overview"),
    DocPage("getting-started", "Getting started"),
    DocPage("routing", "Routes and URLs"),
    DocPage("layouts", "Layouts and containers"),
    DocPage("parallel-routes", "Slots and parallel routes"),
    DocPage("data-loading", "Data, loading and errors"),
    DocPage("query-params", "Query parameters"),
    DocPage("navigation", "Navigation"),
    DocPage("transitions", "Transitions and streaming"),
    DocPage("testing", "Testing routes"),
    DocPage("api-reference", "API reference"),
    DocPage("troubleshooting", "Troubleshooting"),
)

_SLUG_RE = re.compile(r"\]\((?:\./)?([A-Za-z0-9_-]+)\.md(#[^)\s]*)?\)")


def page_by_slug(slug: str) -> DocPage | None:
    return next((page for page in DOC_PAGES if page.slug == slug), None)


def doc_href(slug: str) -> str:
    return "/documentation" if slug == "index" else f"/documentation/{slug}"


def load_doc(slug: str) -> str | None:
    if page_by_slug(slug) is None:
        return None
    path = DOCS_DIR / f"{slug}.md"
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8")


def rewrite_links(text: str) -> str:
    """Point sibling `*.md` links at the matching `/documentation` route; leave everything else alone."""

    def replace(match: re.Match[str]) -> str:
        slug, anchor = match.group(1), match.group(2) or ""
        if page_by_slug(slug) is None:
            return match.group(0)
        return f"]({doc_href(slug)}{anchor})"

    return _SLUG_RE.sub(replace, text)
