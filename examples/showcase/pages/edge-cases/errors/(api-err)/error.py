from edge_helpers import edge_badge, part_card


def error(error: Exception, **_):
    url = "/edge-cases/errors (api-err)"
    return part_card(
        "(api-err) · error.py",
        edge_badge("errors-api-error", url),
        f"{type(error).__name__}: {error}",
    )
