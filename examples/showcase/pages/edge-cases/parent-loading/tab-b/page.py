from edge_helpers import edge_badge, part_card


def page(**_):
    return part_card("Tab B", edge_badge("parent-loading-b", "/edge-cases/parent-loading/tab-b"), "tab-b rendered")
