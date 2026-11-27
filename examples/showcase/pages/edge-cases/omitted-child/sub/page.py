from edge_helpers import edge_badge, part_card


def page(**_):
    url = "/edge-cases/omitted-child/sub"
    return part_card("Sub route", edge_badge("omitted-child-sub", url), "omitted-child/sub rendered.")
