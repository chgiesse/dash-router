from edge_helpers import edge_badge, part_card


def page(**_):
    return part_card("Tab A", edge_badge("parent-loading-a", "/edge-cases/parent-loading/tab-a"), "tab-a rendered")
