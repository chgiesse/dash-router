from __future__ import annotations

from typing import Any, Literal, cast

from dash.development.base_component import Component

from ._components.Link import Link as _GeneratedLink
from ._components.UrlCommit import UrlCommit as _GeneratedUrlCommit
from ._components.UrlParam import UrlParam as _GeneratedUrlParam
from ._components.UrlSegment import UrlSegment as _GeneratedUrlSegment
from .components import ChildContainer

_UNSET = object()


class UrlParam(_GeneratedUrlParam):
    """Sync one prop of ``component`` with the URL query parameter ``param`` (native, no clientside callback).

    ``default`` is the value the param stands for when it is missing from the URL: the param is left out while the
    control has that value. Without it, the default is whatever the layout renders when the URL has no such param.
    Pass it for every param whose default is not empty (``None`` / ``""`` / ``[]``), otherwise a page opened with
    the param already in the URL cannot tell the default apart and writes it (e.g. ``page=1``).
    ``clear`` lists other query params removed whenever this one changes (e.g. ``["page"]``).

    ``group`` defers the write until a :class:`UrlCommit` with the same group is clicked. ``commit_on`` names a
    child prop (e.g. ``"n_submit"``) whose change commits the group; ``set_params`` are written on that commit.
    """

    _children_props = _GeneratedUrlParam._children_props

    def __init__(
        self,
        component: Component,
        param: str,
        *,
        clear: list[str] | None = None,
        prop: str = "value",
        format: Literal["auto", "string", "list", "number", "boolean", "json"] = "auto",
        default: Any = _UNSET,
        history: Literal["push", "replace"] = "push",
        debounce: int = 0,
        two_way: bool = False,
        group: str | None = None,
        commit_on: str | None = None,
        set_params: dict[str, str] | None = None,
        **kwargs: Any,
    ):
        if default is not _UNSET:
            kwargs["default"] = default
        if group is not None:
            kwargs["group"] = group
        if commit_on is not None:
            kwargs["commitOn"] = commit_on
        if set_params is not None:
            kwargs["setParams"] = set_params
        super().__init__(
            children=component,
            param=param,
            prop=prop,
            format=format,
            clear=clear or [],
            history=history,
            debounce=debounce,
            twoWay=two_way,
            **kwargs,
        )


class UrlCommit(_GeneratedUrlCommit):
    """Write URL state when ``prop`` of ``component`` changes (default ``n_clicks``).

    With ``group``: commits the deferred :class:`UrlParam` values of that group; ``set_params`` are written only if
    at least one param of the group has a value, otherwise those keys are removed.
    Without ``group``: always writes ``set_params`` (a button that sets fixed params, e.g. next/prev step).
    ``clear`` params are removed in both cases.
    """

    _children_props = _GeneratedUrlCommit._children_props

    def __init__(
        self,
        component: Component,
        group: str | None = None,
        *,
        prop: str = "n_clicks",
        clear: list[str] | None = None,
        set_params: dict[str, str] | None = None,
        history: Literal["push", "replace"] = "push",
        **kwargs: Any,
    ):
        if group is not None:
            kwargs["group"] = group
        super().__init__(
            children=component,
            prop=prop,
            clear=clear or [],
            setParams=cast(Any, set_params or {}),
            history=history,
            **kwargs,
        )


class UrlSegment(_GeneratedUrlSegment):
    """Sync one prop of ``component`` with the URL path segment after ``base`` (native, no callbacks).

    ``container`` is the :class:`ChildContainer` the component is rendered in; its ``base`` and ``active`` are used
    unless ``base`` is passed explicitly. ``base`` is the browser path of the parent (e.g. ``"/orders/1003"``), the
    segment is written as ``{base}/{value}``. ``default`` is the segment the bare ``base`` URL stands for.
    ``keep_query`` keeps the query string when the segment changes. Back/forward and links update the component.
    """

    _children_props = _GeneratedUrlSegment._children_props

    def __init__(
        self,
        component: Component,
        container: ChildContainer | None = None,
        *,
        base: str | None = None,
        prop: str = "value",
        default: str | None = None,
        history: Literal["push", "replace"] = "push",
        keep_query: bool = True,
        **kwargs: Any,
    ):
        resolved_base = base if base is not None else (container.props.base if container is not None else None)
        if resolved_base is None:
            raise ValueError("UrlSegment needs a base: pass the ChildContainer as the second argument or base=...")
        if container is not None and getattr(component, prop, None) is None:
            value = container.props.active if container.props.active is not None else default
            if value is not None:
                setattr(component, prop, value)
        if default is not None:
            kwargs["default"] = default
        super().__init__(
            children=component,
            base=resolved_base,
            prop=prop,
            history=history,
            keepQuery=keep_query,
            **kwargs,
        )


class Link(_GeneratedLink):
    """In-page navigation link: a click updates the URL without a reload (external and modified clicks are left to
    the browser). ``match="prefix"`` marks the link active on its path and sub-paths, ``"exact"`` only on its path.
    The active link gets ``aria-current="page"`` and ``data-active="true"``.
    """

    _children_props = _GeneratedLink._children_props

    def __init__(
        self,
        children: Component | str,
        href: str,
        *,
        replace: bool = False,
        match: Literal["exact", "prefix"] = "prefix",
        **kwargs: Any,
    ):
        super().__init__(children=children, href=href, replace=replace, match=match, **kwargs)
