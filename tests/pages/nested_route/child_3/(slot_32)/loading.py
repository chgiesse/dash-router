from components import create_box


async def layout(*args, **kwargs):
    return create_box(
        "tests/pages/nested_route/child_3/(slot_32)/loading.py",
        None,
        *args,
        **kwargs,
    )
