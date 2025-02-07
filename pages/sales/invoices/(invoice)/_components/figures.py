import random

import dash_mantine_components as dmc

data = [
    {"name": "USA", "value": random.randint(50, 3000), "color": "indigo.6"},
    {"name": "India", "value": random.randint(50, 3000), "color": "yellow.6"},
    {"name": "Japan", "value": random.randint(50, 3000), "color": "teal.6"},
    {"name": "Other", "value": random.randint(50, 3000), "color": "gray.6"},
]

donut_chart = dmc.DonutChart(
    data=data,
    size=80,
    thickness=30,
    m="auto",
    tooltipDataSource="segment",
    pieProps={"isAnimationActive": True},
)

data_comp = [
    {
        "date": "Mar 22",
        "Apples": random.randint(50, 3000),
        "Oranges": random.randint(50, 3000),
        "Tomatoes": 2452,
    },
    {
        "date": "Mar 23",
        "Apples": 2756,
        "Oranges": 2103,
        "Tomatoes": 2402,
    },
    {
        "date": "Mar 24",
        "Apples": 3322,
        "Oranges": random.randint(50, 3000),
        "Tomatoes": 1821,
    },
    {
        "date": "Mar 25",
        "Apples": random.randint(50, 3000),
        "Oranges": random.randint(50, 3000),
        "Tomatoes": 2809,
    },
    {
        "date": "Mar 26",
        "Apples": 3129,
        "Oranges": random.randint(50, 3000),
        "Tomatoes": random.randint(50, 3000),
    },
]

comp_figure = dmc.CompositeChart(
    h=300,
    data=data,
    dataKey="date",
    withLegend=True,
    maxBarWidth=30,
    series=[
        {"name": "Tomatoes", "color": "rgba(18, 120, 255, 0.2)", "type": "bar"},
        {"name": "Apples", "color": "red.8", "type": "line"},
        {"name": "Oranges", "color": "yellow.8", "type": "area"},
    ],
)


def create_water_chart():
    water_data = [
        {
            "item": "TaxRate",
            "Effective tax rate in %": random.randint(-5, 15),
            "color": "blue",
        },
        {
            "item": "Foreign inc.",
            "Effective tax rate in %": random.randint(-5, 15),
            "color": "teal",
        },
        {"item": "Perm. diff.", "Effective tax rate in %": -3, "color": "teal"},
        {
            "item": "Credits",
            "Effective tax rate in %": random.randint(-5, 15),
            "color": "teal",
        },
        {"item": "Loss carryf.", "Effective tax rate in %": -2, "color": "teal"},
        {
            "item": "Law changes",
            "Effective tax rate in %": random.randint(-5, 15),
            "color": "red",
        },
        {"item": "Reven. adj.", "Effective tax rate in %": 4, "color": "red"},
        {
            "item": "ETR",
            "Effective tax rate in %": 3.5,
            "color": "blue",
            "standalone": True,
        },
    ]

    return dmc.BarChart(
        h=300,
        data=water_data,
        dataKey="item",
        type="waterfall",
        series=[{"name": "Effective tax rate in %", "color": "blue"}],
        withLegend=True,
        barProps={"isAnimationActive": True},
    )


def create_line_chart():
    line_data = [
        {
            "date": "Mar 22",
            "Apples": random.randint(50, 3000),
            "Oranges": 2338,
            "Tomatoes": 2452,
        },
        {"date": "Mar 23", "Apples": 2756, "Oranges": 2103, "Tomatoes": 2402},
        {
            "date": "Mar 24",
            "Apples": 3322,
            "Oranges": random.randint(50, 3000),
            "Tomatoes": 1821,
        },
        {
            "date": "Mar 25",
            "Apples": random.randint(50, 3000),
            "Oranges": random.randint(50, 3000),
            "Tomatoes": 2809,
        },
        {
            "date": "Mar 26",
            "Apples": random.randint(50, 3000),
            "Oranges": 1726,
            "Tomatoes": 2290,
        },
    ]

    return dmc.LineChart(
        h=300,
        dataKey="date",
        data=line_data,
        dotProps={"r": 6, "strokeWidth": 2, "stroke": "#fff"},
        activeDotProps={"r": 8, "strokeWidth": 1, "fill": "#fff"},
        tickLine="none",
        withXAxis=False,
        series=[
            {"name": "Apples", "color": "indigo.6"},
            {"name": "Oranges", "color": "blue.6"},
            {"name": "Tomatoes", "color": "teal.6"},
        ],
        lineProps={
            "isAnimationActive": True,
            "animationDuration": 500,
            "animationEasing": "ease-in-out",
        },
    )


def create_rel_barchart():
    data = [
        {"month": "January", "Smartphones": 1200, "Laptops": 900, "Tablets": 200},
        {"month": "February", "Smartphones": 1900, "Laptops": 1200, "Tablets": 400},
        {"month": "March", "Smartphones": 400, "Laptops": 1000, "Tablets": 200},
        {"month": "April", "Smartphones": 1000, "Laptops": 200, "Tablets": 800},
        {"month": "May", "Smartphones": 800, "Laptops": 1400, "Tablets": 1200},
        {"month": "June", "Smartphones": 750, "Laptops": 600, "Tablets": 1000},
    ]
    return dmc.BarChart(
        h=300,
        dataKey="month",
        data=data,
        type="percent",
        barProps={"isAnimationActive": True, "radius": 50},
        series=[
            {"name": "Smartphones", "color": "violet.6"},
            {"name": "Laptops", "color": "blue.6"},
            {"name": "Tablets", "color": "teal.6"},
        ],
    )
