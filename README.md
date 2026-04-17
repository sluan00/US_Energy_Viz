# U.S. Energy Generation Dashboard

An interactive dashboard exploring shifts in U.S. electricity generation by energy source across all 50 states from 1990 to 2024. Built with Svelte and D3.js.

**Live deployment:** _[TODO: add Netlify URL after deploy]_

## Data Sources

- **Electricity generation by state and energy source** (1990-2024): [EIA Annual Generation State Historical Tables](https://www.eia.gov/electricity/data/state/) (`annual_generation_state.xls`). Filtered to "Total Electric Power Industry" for Coal, Natural Gas, Nuclear, Hydroelectric Conventional, Wind, Solar Thermal and Photovoltaic, and Petroleum.

- **Fuel prices delivered to power plants** (1990-2024): [EIA Monthly Energy Review, Table 9.9](https://www.eia.gov/totalenergy/data/browser/?tbl=T09.09) — Cost of fossil-fuel receipts at electric generating plants in $/MMBtu for Coal, Natural Gas, and Petroleum.

- **Average retail electricity price by state** (1990-2024): [EIA Average Price of Electricity](https://www.eia.gov/electricity/data/state/) (`avgprice_annual.xlsx`, 1990-2020) combined with [EIA Form 861 Historical Summary](https://www.eia.gov/electricity/data/eia861/) (`HS861 2010-.xlsx`, 2010-2024).

- **U.S. state boundaries**: [us-atlas TopoJSON](https://github.com/topojson/us-atlas) (`states-10m.json`).

## Features

- Choropleth map colored by total or source-specific energy generation
- Stacked bar chart showing energy mix composition (national or per-state)
- Top 10 states ranking for the selected energy source
- Line chart with draggable time slider showing fuel commodity prices and average electricity cost
- Crossfiltering: all views are linked via year, energy source, and state selections
