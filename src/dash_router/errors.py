class RouteTreeValidationError(Exception):
    """The route tree is inconsistent (e.g. a static route with children)."""


class RouteConfigConflictError(Exception):
    """A layout is defined both in `RouteConfig` and in its own file."""


class RouteModuleImportError(Exception):
    """A route file failed to import."""


class RouteLayoutMissingError(Exception):
    """A `page.py` or `default.py` does not define `layout`."""
