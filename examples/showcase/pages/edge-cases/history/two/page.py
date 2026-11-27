from edge_helpers import edge_badge, part_card


def page(data: str, **_):
    url = "/edge-cases/history/two"
    return part_card("History · two", edge_badge("history-two", url), f"api.py {data} landed after 0.4 s")
