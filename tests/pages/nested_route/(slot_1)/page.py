from components import create_box


async def layout(*args, **kwargs):
    return create_box(
        "tests/pages/nested_route/(slot_1)/page.py",
        None,
        *args,
        **kwargs,
    )
