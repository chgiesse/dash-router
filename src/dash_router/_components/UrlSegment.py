# AUTO GENERATED FILE - DO NOT EDIT

import typing  # noqa: F401
from typing_extensions import TypedDict, NotRequired, Literal # noqa: F401
from dash.development.base_component import Component, _explicitize_args
try:
    from dash.types import NumberType  # noqa: F401
except ImportError:
    # Backwards compatibility for dash<=4.1.0
    if typing.TYPE_CHECKING:
        raise
    NumberType = typing.Union[  # noqa: F401
        typing.SupportsFloat, typing.SupportsInt, typing.SupportsComplex
    ]

ComponentSingleType = typing.Union[str, int, float, Component, None]
ComponentType = typing.Union[
    ComponentSingleType,
    typing.Sequence[ComponentSingleType],
]


class UrlSegment(Component):
    """An UrlSegment component.
Syncs one prop of its child with a URL path segment, e.g. the active tab of `/orders/1003/<tab>`

Keyword arguments:

- children (a list of or a singular dash component, string or number; required):
    A single component whose prop is synced with a URL path segment.

- id (string; optional):
    Unique ID to identify this component in Dash callbacks.

- aria-* (string; optional):
    Wild card aria attributes.

- base (string; required):
    Browser path of the parent, without trailing slash, e.g.
    \"/orders/1003\" (\"\" for the root).

- data-* (string; optional):
    Wild card data attributes.

- default (string; optional):
    Segment the bare `base` URL stands for; selecting it writes `base`
    without the segment.

- history (a value equal to: 'replace', 'push'; optional):
    \"push\" adds a browser history entry, \"replace\" does not.
    Default \"push\".

- keepQuery (boolean; optional):
    Keep the query string when the segment is written. Default True.

- loading_state (dict; optional):
    Object that holds the loading state object coming from
    dash-renderer. For use with dash<3.

    `loading_state` is a dict with keys:

    - is_loading (boolean; required):
        Determines if the component is loading or not.

    - prop_name (string; required):
        Holds which property is loading.

    - component_name (string; required):
        Holds the name of the component that is loading.

- prop (string; optional):
    Prop of the child that is synced. Default \"value\".

- tabIndex (number; optional):
    tab-index."""
    _children_props: typing.List[str] = []
    _base_nodes = ['children']
    _namespace = 'dash_router'
    _type = 'UrlSegment'
    LoadingState = TypedDict(
        "LoadingState",
            {
            "is_loading": bool,
            "prop_name": str,
            "component_name": str
        }
    )


    def __init__(
        self,
        children: typing.Optional[ComponentType] = None,
        base: typing.Optional[str] = None,
        prop: typing.Optional[str] = None,
        default: typing.Optional[str] = None,
        history: typing.Optional[Literal["replace", "push"]] = None,
        keepQuery: typing.Optional[bool] = None,
        id: typing.Optional[typing.Union[str, dict]] = None,
        tabIndex: typing.Optional[NumberType] = None,
        loading_state: typing.Optional["LoadingState"] = None,
        **kwargs
    ):
        self._prop_names = ['children', 'id', 'aria-*', 'base', 'data-*', 'default', 'history', 'keepQuery', 'loading_state', 'prop', 'tabIndex']
        self._valid_wildcard_attributes =            ['data-', 'aria-']
        self.available_properties = ['children', 'id', 'aria-*', 'base', 'data-*', 'default', 'history', 'keepQuery', 'loading_state', 'prop', 'tabIndex']
        self.available_wildcard_properties =            ['data-', 'aria-']
        _explicit_args = kwargs.pop('_explicit_args')
        _locals = locals()
        _locals.update(kwargs)  # For wildcard attrs and excess named props
        args = {k: _locals[k] for k in _explicit_args if k != 'children'}

        for k in ['base']:
            if k not in args:
                raise TypeError(
                    'Required argument `' + k + '` was not specified.')

        if 'children' not in _explicit_args:
            raise TypeError('Required argument children was not specified.')

        super(UrlSegment, self).__init__(children=children, **args)

setattr(UrlSegment, "__init__", _explicitize_args(UrlSegment.__init__))
