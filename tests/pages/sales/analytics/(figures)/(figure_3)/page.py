from components import create_box


async def layout(*args, **kwargs):
    return create_box(
        "tests/pages/sales/analytics/(figures)/(figure_3)/page.py",
        None,
        *args,
        **kwargs,
    )
