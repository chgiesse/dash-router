import dash_mantine_components as dmc

bar_data = data = [
    {"month": "Amazon", "Smartphones": 1200, "Laptops": 900, "Tablets": 200},
    {"month": "Apple", "Smartphones": 1900, "Laptops": 1200, "Tablets": 400},
    {"month": "Nvidia", "Smartphones": 400, "Laptops": 1000, "Tablets": 200},
    {"month": "AMD", "Smartphones": 1000, "Laptops": 200, "Tablets": 800},
    {"month": "Microsoft", "Smartphones": 800, "Laptops": 1400, "Tablets": 1200},
    {"month": "SAP", "Smartphones": 750, "Laptops": 600, "Tablets": 1000},
]

bar_chart = dmc.BarChart(
    h=300,
    dataKey="month",
    data=bar_data,
    orientation="vertical",
    yAxisProps={"width": 80},
    series=[{"name": "Smartphones", "color": "violet.6"}],
    barProps={"isAnimationActive": True, "radius": 50},
    gridAxis="none",
)
