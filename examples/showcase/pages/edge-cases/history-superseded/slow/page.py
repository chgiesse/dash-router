from edge_helpers import edge_badge, part_card

URL = "/edge-cases/history-superseded/slow"


def page(data: str, **_):
    return part_card("Slow", edge_badge("history-superseded-slow", URL), f"Landed: {data}. Its history entry must not exist.")
