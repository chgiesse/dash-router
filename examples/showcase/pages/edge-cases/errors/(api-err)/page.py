from edge_helpers import edge_badge, part_card


def page(data: str, **_):
    return part_card("(api-err)", edge_badge("errors-api-ok", "/edge-cases/errors (api-err)"), data)
