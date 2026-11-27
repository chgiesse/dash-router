from importlib.metadata import version as _version

from .components import ChildContainer, LazyContainer, RootContainer, SlotContainer
from .core.matcher import MatchedNode, MatchedTree, PatchOp, PatchTarget, TransitionPlan
from .core.tree import RouteConfig, RouteNode, RouteTree
from .errors import RouteConfigConflictError, RouteLayoutMissingError, RouteModuleImportError, RouteTreeValidationError
from .navigation import RouteId, Url, get_current_url, navigate, url_for
from .router import DashRouter
from .testing import RouteTester, TransitionResult, assert_transition
from .url_state import Link, UrlCommit, UrlParam, UrlSegment

__version__ = _version("dash-router")

# Bundle with the `Link`, `UrlParam`, `UrlSegment` and `UrlCommit` React components, served by Dash.
_js_dist = [{"relative_package_path": "dash_router.min.js", "namespace": "dash_router"}]

__all__ = [
    "ChildContainer",
    "DashRouter",
    "LazyContainer",
    "Link",
    "MatchedNode",
    "MatchedTree",
    "PatchOp",
    "PatchTarget",
    "RootContainer",
    "RouteConfig",
    "RouteConfigConflictError",
    "RouteId",
    "RouteLayoutMissingError",
    "RouteModuleImportError",
    "RouteNode",
    "RouteTester",
    "RouteTree",
    "RouteTreeValidationError",
    "SlotContainer",
    "TransitionPlan",
    "TransitionResult",
    "Url",
    "UrlCommit",
    "UrlParam",
    "UrlSegment",
    "assert_transition",
    "get_current_url",
    "navigate",
    "url_for",
]
