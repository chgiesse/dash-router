from collections import defaultdict

import dash_mantine_components as dmc

from data import CUSTOMERS
from ui import section


def page(**_):
    groups: dict[str, list[str]] = defaultdict(list)
    for c in CUSTOMERS.values():
        groups[c.segment].append(c.name)
    return section(
        "Segments",
        dmc.SimpleGrid(
            [
                dmc.Paper(
                    [dmc.Text(seg, fw=600), dmc.Text(f"{len(names)} customers", size="xs", c="dimmed"), dmc.Text(", ".join(names), size="sm", mt="xs")],
                    withBorder=True,
                    p="sm",
                )
                for seg, names in sorted(groups.items())
            ],
            cols={"base": 1, "md": 3},
        ),
        features=("(inspector) -> default.py here", "(pinned) has its own segments route"),
    )
