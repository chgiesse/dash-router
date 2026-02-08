from components import create_box


async def layout(*args, **kwargs):
    return create_box(
        "tests/pages/sales/invoices/(overview)/page.py",
        None,
        *args,
        **kwargs,
    )
