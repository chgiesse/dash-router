from edge_helpers import edge_badge, part_card


def error(error: Exception, **_):
    url = "/edge-cases/errors (gen-err)"
    return part_card(
        "(gen-err) · error.py",
        edge_badge("errors-gen-error", url),
        f"{type(error).__name__}: {error}",
    )
