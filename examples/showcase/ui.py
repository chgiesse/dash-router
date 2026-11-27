"""Shared UI building blocks for the showcase."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal

import dash_mantine_components as dmc
from dash import html


@dataclass(frozen=True)
class SkeletonColumn:
    """Column specification for :func:`table_skeleton`."""

    label: str
    widths: tuple[str | int, ...] = ("70%", "56%", "82%", "64%", "76%", "60%")
    kind: Literal["text", "id", "pill", "number"] = "text"
    align: Literal["left", "right", "center"] = "left"
    width: str | int | None = None


def rendered_badge(label: str = "rendered") -> dmc.Badge:
    """Server time of this render. If it does not change, the section was not re-rendered."""
    stamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    return dmc.Badge(
        f"{label} {stamp}",
        variant="light",
        color="gray",
        size="sm",
        radius="sm",
        className="rendered-badge",
        style={"textTransform": "none", "fontFamily": "monospace"},
    )


def feature_tags(*features: str) -> dmc.Group:
    return dmc.Group(
        [dmc.Badge(f, variant="dot", color="indigo", size="sm") for f in features],
        gap=6,
    )


def section(
    title: str,
    children: Any,
    *,
    features: tuple[str, ...] = (),
    right: Any = None,
    **card_props: Any,
) -> dmc.Card:
    header = dmc.Group(
        [
            dmc.Stack([dmc.Text(title, fw=600), feature_tags(*features)] if features else [dmc.Text(title, fw=600)], gap=4),
            dmc.Group([right, rendered_badge()] if right is not None else [rendered_badge()], gap="xs"),
        ],
        justify="space-between",
        align="flex-start",
        mb="sm",
    )
    return dmc.Card([header, children], withBorder=True, radius="md", padding="md", **card_props)


def loading_badge(label: str = "loading.py") -> dmc.Badge:
    return dmc.Badge(label, color="yellow", variant="light", size="sm")


def kpi_card(label: str, value: float, color: str = "dimmed", *, currency: bool = False) -> dmc.Card:
    """KPI card whose number rolls to a new value.

    `(kpis)/loading.py` renders the same card with `value=0`, so when the data arrives Dash updates the
    `RollingNumber` in place and its digits roll up to the real value (it does not animate on first render).
    """
    number_format: dict[str, Any] = {"thousandSeparator": True}
    if currency:
        number_format.update(prefix="$", decimalScale=2, fixedDecimalScale=True)
    return dmc.Card(
        [
            dmc.Text(label, size="xs", c="dimmed", tt="uppercase", fw=600),
            dmc.Title(dmc.RollingNumber(value=value, **number_format), order=3, c=color),
        ],
        withBorder=True,
        padding="md",
    )


def loading_section(
    title: str | Any,
    children: Any,
    *,
    features: tuple[str, ...] = (),
    badge: str = "loading.py",
    **card_props: Any,
) -> dmc.Card:
    """Card shell matching :func:`section` for `loading.py` boundaries."""
    title_el = dmc.Text(title, fw=600) if isinstance(title, str) else title
    header = dmc.Group(
        [
            dmc.Stack([title_el, feature_tags(*features)] if features else [title_el], gap=4),
            loading_badge(badge),
        ],
        justify="space-between",
        align="flex-start",
        mb="sm",
    )
    return dmc.Card([header, children], withBorder=True, radius="md", padding="md", **card_props)


def _skeleton_cell(col: SkeletonColumn, row_idx: int) -> dmc.TableTd:
    w = col.widths[row_idx % len(col.widths)]
    if col.kind == "pill":
        skel = dmc.Skeleton(height=20, width=w, radius="xl")
    else:
        skel = dmc.Skeleton(height=14, width=w, radius="sm")

    flex_style: dict[str, str] = {"display": "flex", "alignItems": "center"}
    if col.align == "right":
        flex_style["justifyContent"] = "flex-end"
    elif col.align == "center":
        flex_style["justifyContent"] = "center"
    return dmc.TableTd(dmc.Box(skel, h=22, style=flex_style), ta=col.align)


def table_head(columns: Sequence[str | SkeletonColumn]) -> dmc.TableThead:
    cols = [c if isinstance(c, SkeletonColumn) else SkeletonColumn(c) for c in columns]
    return dmc.TableThead(dmc.TableTr([dmc.TableTh(c.label, ta=c.align, w=c.width) for c in cols]))


def table_skeleton_rows(
    columns: Sequence[str | SkeletonColumn],
    *,
    rows: int = 6,
    fade_tail: bool = True,
) -> list[dmc.TableTr]:
    """Skeleton body rows matching `columns` (reusable in tables streaming via `set_props`)."""
    cols = [c if isinstance(c, SkeletonColumn) else SkeletonColumn(c) for c in columns]
    body_rows: list[dmc.TableTr] = []
    for i in range(rows):
        style: dict[str, Any] | None = None
        if fade_tail and rows >= 5:
            if i == rows - 1:
                style = {"opacity": 0.45}
            elif i == rows - 2:
                style = {"opacity": 0.72}
        body_rows.append(dmc.TableTr([_skeleton_cell(c, i) for c in cols], style=style))
    return body_rows


def table_skeleton(
    columns: Sequence[str | SkeletonColumn],
    *,
    rows: int = 6,
    vertical_spacing: str | int | None = None,
    fade_tail: bool = True,
) -> dmc.Table:
    """Table skeleton with fixed column widths, matching row heights, pill badges and tail fade."""
    cols = [c if isinstance(c, SkeletonColumn) else SkeletonColumn(c) for c in columns]
    head = table_head(cols)
    body_rows = table_skeleton_rows(cols, rows=rows, fade_tail=fade_tail)

    kwargs: dict[str, Any] = {}
    if vertical_spacing is not None:
        kwargs["verticalSpacing"] = vertical_spacing
    return dmc.Table(
        [head, dmc.TableTbody(body_rows)],
        layout="fixed",
        className="showcase-table",
        **kwargs,
    )


def graph_spinner(
    label: str = "Loading chart…",
    *,
    height: int | str = 240,
    size: str | int = "md",
    color: str = "indigo",
) -> dmc.Center:
    """Centered spinner reserving the chart's height while series data loads."""
    return dmc.Center(
        dmc.Stack(
            [
                dmc.Loader(type="oval", size=size, color=color),
                dmc.Text(label, size="xs", c="dimmed"),
            ],
            align="center",
            gap="xs",
        ),
        h=height,
    )


def skeleton_block(lines: int = 4, height: int = 14) -> dmc.Stack:
    return dmc.Stack([dmc.Skeleton(height=height, radius="sm") for _ in range(lines)], gap="xs")


def loading_card(title: str, lines: int = 4) -> dmc.Card:
    """Static skeleton used by `loading.py` files. The server sends it in frame 0 of the navigation."""
    return loading_section(title, skeleton_block(lines))


def link(label: str, href: str, **props: Any) -> dmc.Anchor:
    return dmc.Anchor(label, href=href, underline="hover", **props)


def money(value: float) -> str:
    return f"${value:,.2f}"


def code(text: str) -> html.Code:
    return dmc.Code(text)  # type: ignore[return-value]
