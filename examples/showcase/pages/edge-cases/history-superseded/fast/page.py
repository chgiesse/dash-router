from edge_helpers import edge_badge, part_card

URL = "/edge-cases/history-superseded/fast"


def page(**_):
    return part_card("Fast", edge_badge("history-superseded-fast", URL), "Fast landed. It replaced Slow's history entry.")
