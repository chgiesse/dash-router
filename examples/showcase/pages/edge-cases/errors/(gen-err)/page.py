from collections.abc import AsyncIterator
from typing import Any

from edge_helpers import edge_badge, edge_sleep, part_card


class GeneratorError(RuntimeError):
    pass


async def page(**_: Any) -> AsyncIterator[Any]:
    yield part_card("(gen-err) · frame 1", edge_badge("errors-gen-frame", "/edge-cases/errors (gen-err)"), "frame 1")
    await edge_sleep(0.5)
    raise GeneratorError("gen-err: stream broke after frame 1")
