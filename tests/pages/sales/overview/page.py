from flash_router import RouteConfig

from components import create_box

config = RouteConfig(path_template="<...rest>")


async def layout(rest: list | None = None, *args, **kwargs):
    return create_box(
        "tests/pages/sales/overview/page.py",
        None,
        rest=rest,
        *args,
        **kwargs,
    )
