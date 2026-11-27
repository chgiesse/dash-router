from edge_helpers import edge_badge, part_card


def page(**_):
    url = "/edge-cases/nested-lazy/two"
    return part_card("two · no api", edge_badge("nested-lazy-two", url), "two rendered without a lazy boundary.")
