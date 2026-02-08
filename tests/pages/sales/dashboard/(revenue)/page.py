from components import create_box


async def layout(*args, **kwargs):
    return create_box(
        "tests/pages/sales/dashboard/(revenue)/page.py",
        None,
        *args,
        **kwargs,
    )
