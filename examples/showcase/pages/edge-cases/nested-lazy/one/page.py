from edge_helpers import edge_badge, part_card


def page(data: str, **_):
    url = "/edge-cases/nested-lazy/one"
    return part_card("one · inner boundary landed", edge_badge("nested-lazy-one", url), data)
