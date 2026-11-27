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


class UrlCommit(Component):
    """An UrlCommit component.
Writes a group of deferred UrlParam values (and/or fixed parameters) to the URL when its child fires

Keyword arguments:

- children (a list of or a singular dash component, string or number; required):
    A single component that commits, e.g. an apply button.

- id (string; optional):
    Unique ID to identify this component in Dash callbacks.

- aria-* (string; optional):
    Wild card aria attributes.

- clear (list of strings; optional):
    Query parameters removed on commit (e.g. [\"page\"]).

- data-* (string; optional):
    Wild card data attributes.

- group (string; optional):
    Group of UrlParam components (`group=...`) that is written to the
    URL. Without a group only `setParams` / `clear` are applied.

- history (a value equal to: 'replace', 'push'; default 'push'):
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

- prop (string; default 'n_clicks'):
    Prop of the child that triggers the commit when it changes.
    Default \"n_clicks\".

- setParams (dict with strings as keys and values of type string; optional):
    Parameters written on commit. With a group only if at least one of
    its parameters has a value (otherwise they are removed).

- tabIndex (number; optional):
    tab-index."""
    _children_props: typing.List[str] = []
    _base_nodes = ['children']
    _namespace = 'dash_router'
    _type = 'UrlCommit'
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
        group: typing.Optional[str] = None,
        prop: typing.Optional[str] = None,
        clear: typing.Optional[typing.Sequence[str]] = None,
        setParams: typing.Optional[typing.Dict[typing.Union[str, float, int], str]] = None,
        history: typing.Optional[Literal["replace", "push"]] = None,
        id: typing.Optional[typing.Union[str, dict]] = None,
        tabIndex: typing.Optional[NumberType] = None,
        loading_state: typing.Optional["LoadingState"] = None,
        **kwargs
    ):
        self._prop_names = ['children', 'id', 'aria-*', 'clear', 'data-*', 'group', 'history', 'loading_state', 'prop', 'setParams', 'tabIndex']
        self._valid_wildcard_attributes =            ['data-', 'aria-']
        self.available_properties = ['children', 'id', 'aria-*', 'clear', 'data-*', 'group', 'history', 'loading_state', 'prop', 'setParams', 'tabIndex']
        self.available_wildcard_properties =            ['data-', 'aria-']
        _explicit_args = kwargs.pop('_explicit_args')
        _locals = locals()
        _locals.update(kwargs)  # For wildcard attrs and excess named props
        args = {k: _locals[k] for k in _explicit_args if k != 'children'}

        if 'children' not in _explicit_args:
            raise TypeError('Required argument children was not specified.')

        super(UrlCommit, self).__init__(children=children, **args)

setattr(UrlCommit, "__init__", _explicitize_args(UrlCommit.__init__))
