from edge_helpers import edge_badge, part_card


def page(data: str, **_):
    url = "/edge-cases/history/one"
    return part_card("History · one", edge_badge("history-one", url), f"api.py {data} landed after 0.2 s")
