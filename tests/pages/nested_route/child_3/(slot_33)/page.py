from components import create_box


async def layout(*args, **kwargs):
    return create_box(
        "tests/pages/nested_route/child_3/(slot_33)/page.py",
        None,
        *args,
        **kwargs,
    )
