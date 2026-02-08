from components import create_box


async def layout(*args, **kwargs):
    return create_box(
        "tests/pages/sales/invoices/[invoice_id]/positions/loading.py",
        None,
        *args,
        **kwargs,
    )
