from .._components.table import create_invoice_table


async def layout(**kwargs):
    # def layout(**kwargs):
    # await asyncio.sleep(1.2)
    return create_invoice_table()
