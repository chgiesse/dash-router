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


class UrlParam(Component):
    """An UrlParam component.
Syncs one prop of its child with a URL query parameter, without callbacks

Keyword arguments:

- children (a list of or a singular dash component, string or number; required):
    A single component whose prop is synced with the URL.

- id (string; optional):
    Unique ID to identify this component in Dash callbacks.

- aria-* (string; optional):
    Wild card aria attributes.

- clear (list of strings; optional):
    Query parameters removed whenever this parameter is written (e.g.
    [\"page\"]).

- commitOn (string; optional):
    Prop of the child that commits the group when it changes, e.g.
    \"n_submit\".

- data-* (string; optional):
    Wild card data attributes.

- debounce (number; optional):
    Wait this many milliseconds after the last change before writing
    the URL. Default 0.

- default (boolean | number | string | dict | list; optional):
    Value the parameter stands for when it is missing from the URL; it
    is left out of the URL while the child has it. Defaults to the
    value the layout renders when the URL has no such parameter.

- format (a value equal to: 'string', 'number', 'boolean', 'auto', 'list', 'json'; optional):
    How the value is written to the URL: lists comma separated,
    \"json\" for objects. \"auto\" infers it from the child's value.
    Default \"auto\".

- group (string; optional):
    Defer the write until the group is committed by a UrlCommit (or
    `commitOn`).

- history (a value equal to: 'replace', 'push'; optional):
    \"push\" adds a browser history entry, \"replace\" does not.
    Default \"push\".

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

- param (string; required):
    Name of the URL query parameter.

- prop (string; optional):
    Prop of the child that is synced. Default \"value\".

- setParams (dict with strings as keys and values of type string; optional):
    Parameters written on a commit triggered via `commitOn`, only if
    the group has a value.

- tabIndex (number; optional):
    tab-index.

- twoWay (boolean; optional):
    Also follow later URL changes (back/forward, other parameters
    clearing this one). Default False."""
    _children_props: typing.List[str] = []
    _base_nodes = ['children']
    _namespace = 'dash_router'
    _type = 'UrlParam'
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
        param: typing.Optional[str] = None,
        prop: typing.Optional[str] = None,
        format: typing.Optional[Literal["string", "number", "boolean", "auto", "list", "json"]] = None,
        clear: typing.Optional[typing.Sequence[str]] = None,
        default: typing.Optional[typing.Any] = None,
        history: typing.Optional[Literal["replace", "push"]] = None,
        debounce: typing.Optional[NumberType] = None,
        twoWay: typing.Optional[bool] = None,
        group: typing.Optional[str] = None,
        commitOn: typing.Optional[str] = None,
        setParams: typing.Optional[typing.Dict[typing.Union[str, float, int], str]] = None,
        id: typing.Optional[typing.Union[str, dict]] = None,
        tabIndex: typing.Optional[NumberType] = None,
        loading_state: typing.Optional["LoadingState"] = None,
        **kwargs
    ):
        self._prop_names = ['children', 'id', 'aria-*', 'clear', 'commitOn', 'data-*', 'debounce', 'default', 'format', 'group', 'history', 'loading_state', 'param', 'prop', 'setParams', 'tabIndex', 'twoWay']
        self._valid_wildcard_attributes =            ['data-', 'aria-']
        self.available_properties = ['children', 'id', 'aria-*', 'clear', 'commitOn', 'data-*', 'debounce', 'default', 'format', 'group', 'history', 'loading_state', 'param', 'prop', 'setParams', 'tabIndex', 'twoWay']
        self.available_wildcard_properties =            ['data-', 'aria-']
        _explicit_args = kwargs.pop('_explicit_args')
        _locals = locals()
        _locals.update(kwargs)  # For wildcard attrs and excess named props
        args = {k: _locals[k] for k in _explicit_args if k != 'children'}

        for k in ['param']:
            if k not in args:
                raise TypeError(
                    'Required argument `' + k + '` was not specified.')

        if 'children' not in _explicit_args:
            raise TypeError('Required argument children was not specified.')

        super(UrlParam, self).__init__(children=children, **args)

setattr(UrlParam, "__init__", _explicitize_args(UrlParam.__init__))
