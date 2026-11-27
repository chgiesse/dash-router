from edge_helpers import edge_badge, part_card

URL = "/edge-cases/history-superseded"


def page(**_):
    return part_card("Index", edge_badge("history-superseded-index", URL), "Pick Slow, then Fast before Slow lands.")
