from components import create_box


async def layout(rest: list | None = None, *args, **kwargs):
    return create_box(
        "tests/pages/files/[__rest]/page.py",
        None,
        rest=rest,
        *args,
        **kwargs,
    )
