from components import create_box


async def layout(*args, **kwargs):
    return create_box(
        "tests/pages/sales/dashboard/(ranks)/page.py",
        None,
        *args,
        **kwargs,
    )
