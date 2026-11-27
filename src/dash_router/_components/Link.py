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


class Link(Component):
    """A Link component.
Navigation link that updates the URL in-page (no reload) and marks itself active

Keyword arguments:

- children (a list of or a singular dash component, string or number; optional):
    Content of the link.

- id (string; optional):
    Unique ID to identify this component in Dash callbacks.

- aria-* (string; optional):
    Wild card aria attributes.

- className (string; optional):
    CSS class name.

- data-* (string; optional):
    Wild card data attributes.

- href (string; required):
    Target URL. Same-origin targets navigate in-page without a reload.

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

- match (a value equal to: 'exact', 'prefix'; default 'prefix'):
    \"exact\" matches the pathname, \"prefix\" also matches sub-paths
    (href \"/\" only matches \"/\"). Default \"prefix\".

- replace (boolean; default False):
    Replace the current history entry instead of adding one. Default
    False.

- tabIndex (number; optional):
    tab-index.

- target (string; optional):
    Anchor target, e.g. \"_blank\". Targets other than \"_self\" are
    left to the browser.

- title (string; optional):
    Tooltip text."""
    _children_props: typing.List[str] = []
    _base_nodes = ['children']
    _namespace = 'dash_router'
    _type = 'Link'
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
        href: typing.Optional[str] = None,
        replace: typing.Optional[bool] = None,
        match: typing.Optional[Literal["exact", "prefix"]] = None,
        target: typing.Optional[str] = None,
        title: typing.Optional[str] = None,
        className: typing.Optional[str] = None,
        style: typing.Optional[typing.Any] = None,
        id: typing.Optional[typing.Union[str, dict]] = None,
        tabIndex: typing.Optional[NumberType] = None,
        loading_state: typing.Optional["LoadingState"] = None,
        **kwargs
    ):
        self._prop_names = ['children', 'id', 'aria-*', 'className', 'data-*', 'href', 'loading_state', 'match', 'replace', 'style', 'tabIndex', 'target', 'title']
        self._valid_wildcard_attributes =            ['data-', 'aria-']
        self.available_properties = ['children', 'id', 'aria-*', 'className', 'data-*', 'href', 'loading_state', 'match', 'replace', 'style', 'tabIndex', 'target', 'title']
        self.available_wildcard_properties =            ['data-', 'aria-']
        _explicit_args = kwargs.pop('_explicit_args')
        _locals = locals()
        _locals.update(kwargs)  # For wildcard attrs and excess named props
        args = {k: _locals[k] for k in _explicit_args if k != 'children'}

        for k in ['href']:
            if k not in args:
                raise TypeError(
                    'Required argument `' + k + '` was not specified.')

        super(Link, self).__init__(children=children, **args)

setattr(Link, "__init__", _explicitize_args(Link.__init__))
