"""
Data processing script for U.S. Energy Generation Dashboard.
Downloads and processes EIA data into clean CSVs for the Svelte/D3 frontend.

Data Sources:
  1. EIA Annual Generation by State (1990-2024):
     https://www.eia.gov/electricity/data/state/annual_generation_state.xls

  2. EIA Fuel Prices - Monthly Energy Review Table 9.9 (1973-2025):
     https://www.eia.gov/totalenergy/data/browser/csv.php?tbl=T09.09

  3. EIA Average Retail Electricity Price by State:
     - 1990-2020: https://www.eia.gov/electricity/data/state/avgprice_annual.xlsx
     - 2010-2024: https://www.eia.gov/electricity/data/state/xls/861/HS861%202010-.xlsx

  4. US States TopoJSON:
     https://cdn.jsdelivr.net/npm/us-atlas@3/states-10m.json

Requirements:
  pip install pandas openpyxl xlrd requests
"""

import pandas as pd
import requests
from pathlib import Path

RAW_DIR = Path(__file__).parent
PUBLIC_DIR = RAW_DIR.parent / "public"
PUBLIC_DIR.mkdir(exist_ok=True)


# =============================================================================
# 1. Download raw data files
# =============================================================================

def download_file(url, filename):
    filepath = RAW_DIR / filename
    if filepath.exists():
        print(f"  Skipping {filename} (already exists)")
        return filepath
    print(f"  Downloading {filename}...")
    resp = requests.get(url)
    resp.raise_for_status()
    filepath.write_bytes(resp.content)
    print(f"  Saved {filename} ({len(resp.content) / 1024:.0f} KB)")
    return filepath


def download_all():
    print("Downloading raw data files...")
    download_file(
        "https://www.eia.gov/electricity/data/state/annual_generation_state.xls",
        "annual_generation_state.xls"
    )
    download_file(
        "https://www.eia.gov/totalenergy/data/browser/csv.php?tbl=T09.09",
        "fuel_prices_raw.csv"
    )
    download_file(
        "https://www.eia.gov/electricity/data/state/avgprice_annual.xlsx",
        "avgprice_annual.xlsx"
    )
    download_file(
        "https://www.eia.gov/electricity/data/state/xls/861/HS861%202010-.xlsx",
        "hs861.xlsx"
    )
    download_file(
        "https://cdn.jsdelivr.net/npm/us-atlas@3/states-10m.json",
        str(PUBLIC_DIR / "us-states.json")
    )
    # us-states.json goes directly to public/
    src = RAW_DIR / str(PUBLIC_DIR / "us-states.json")
    if not (PUBLIC_DIR / "us-states.json").exists():
        resp = requests.get("https://cdn.jsdelivr.net/npm/us-atlas@3/states-10m.json")
        (PUBLIC_DIR / "us-states.json").write_bytes(resp.content)
        print("  Saved us-states.json to public/")


# =============================================================================
# 2. Process generation data
# =============================================================================

def process_generation():
    """
    Reads annual_generation_state.xls and produces generation.csv with columns:
    year, state, source, generation
    Filters to 'Total Electric Power Industry' and key energy sources.
    """
    print("Processing generation data...")
    df = pd.read_excel(
        RAW_DIR / "annual_generation_state.xls",
        skiprows=1  # First row is a title/metadata row
    )
    df.columns = ["year", "state", "producer", "source", "generation"]

    # Filter to total electric power industry
    df = df[df["producer"] == "Total Electric Power Industry"]

    # Keep only key energy sources
    source_rename = {
        "Hydroelectric Conventional": "Hydro",
        "Solar Thermal and Photovoltaic": "Solar",
    }
    keep_sources = [
        "Total", "Coal", "Natural Gas", "Nuclear",
        "Hydroelectric Conventional", "Wind",
        "Solar Thermal and Photovoltaic", "Petroleum"
    ]
    df = df[df["source"].isin(keep_sources)]
    df["source"] = df["source"].replace(source_rename)

    # Filter to US states (2-letter codes), exclude US total and DC
    df = df[df["state"].str.len() == 2]
    df = df[~df["state"].isin(["US", "DC"])]

    # Filter year range
    df = df[(df["year"] >= 1990) & (df["year"] <= 2024)]

    # Fill missing generation with 0
    df["generation"] = pd.to_numeric(df["generation"], errors="coerce").fillna(0).astype(int)

    # Output
    out = df[["year", "state", "source", "generation"]]
    out.to_csv(PUBLIC_DIR / "generation.csv", index=False)
    print(f"  Wrote {len(out)} rows to public/generation.csv")


# =============================================================================
# 3. Process fuel prices
# =============================================================================

def process_fuel_prices():
    """
    Reads EIA Table 9.9 CSV and produces fuel-prices.csv with columns:
    year, fuel, price

    Series codes:
      CLERDUS = Coal ($/MMBtu at power plants)
      NGERDUS = Natural Gas ($/MMBtu at power plants)
      PAERDUS = Petroleum ($/MMBtu at power plants)

    Annual rows are identified by YYYYMM ending in '13' (e.g., 199013).
    """
    print("Processing fuel prices...")
    df = pd.read_csv(RAW_DIR / "fuel_prices_raw.csv")

    series_map = {
        "CLERDUS": "Coal",
        "NGERDUS": "Natural Gas",
        "PAERDUS": "Petroleum",
    }

    df = df[df["MSN"].isin(series_map.keys())]
    df["YYYYMM"] = df["YYYYMM"].astype(str)
    df = df[df["YYYYMM"].str.endswith("13")]  # Annual rows only
    df = df[df["Value"] != "Not Available"]

    df["year"] = df["YYYYMM"].str[:4].astype(int)
    df["fuel"] = df["MSN"].map(series_map)
    df["price"] = pd.to_numeric(df["Value"])

    df = df[(df["year"] >= 1990) & (df["year"] <= 2024)]

    out = df[["year", "fuel", "price"]].sort_values(["year", "fuel"])
    out.to_csv(PUBLIC_DIR / "fuel-prices.csv", index=False)
    print(f"  Wrote {len(out)} rows to public/fuel-prices.csv")


# =============================================================================
# 4. Process electricity prices
# =============================================================================

def process_electricity_prices():
    """
    Combines two EIA sources to produce electricity-prices.csv with columns:
    year, state, residential, commercial, industrial, total

    - avgprice_annual.xlsx: 1990-2020 (state-level, by sector)
    - hs861.xlsx: 2010-2024 (state-level, by sector, from Form 861)

    Uses hs861 for 2010-2024 and avgprice for 1990-2009 to avoid overlap.
    """
    print("Processing electricity prices...")

    # --- HS861: 2010-2024 ---
    df_hs = pd.read_excel(
        RAW_DIR / "hs861.xlsx",
        sheet_name="Total Electric Industry",
        skiprows=2  # Skip title and unit rows
    )
    # Columns: Year, STATE, then 4 groups of (Revenue, Sales, Customers, Price)
    # for Residential, Commercial, Industrial, Transportation, Total
    # Price columns are at indices 5, 9, 13, 17, 21
    df_hs.columns = range(len(df_hs.columns))
    df_hs = df_hs[df_hs[1].astype(str).str.len() == 2]  # State abbreviations only
    df_hs = df_hs[~df_hs[1].isin(["US"])]
    df_hs = df_hs[(df_hs[0] >= 2010) & (df_hs[0] <= 2024)]

    rows_hs = []
    for _, row in df_hs.iterrows():
        rows_hs.append({
            "year": int(row[0]),
            "state": row[1],
            "residential": pd.to_numeric(row[5], errors="coerce") or 0,
            "commercial": pd.to_numeric(row[9], errors="coerce") or 0,
            "industrial": pd.to_numeric(row[13], errors="coerce") or 0,
            "total": pd.to_numeric(row[21], errors="coerce") or 0,
        })
    df_new = pd.DataFrame(rows_hs)

    # --- avgprice_annual.xlsx: 1990-2009 ---
    df_old = pd.read_excel(
        RAW_DIR / "avgprice_annual.xlsx",
        skiprows=1  # Skip title row
    )
    df_old.columns = ["year", "state", "producer", "residential", "commercial",
                       "industrial", "transportation", "other", "total"]
    df_old = df_old[df_old["producer"] == "Total Electric Industry"]
    df_old = df_old[df_old["state"].astype(str).str.len() == 2]
    df_old = df_old[(df_old["year"] >= 1990) & (df_old["year"] < 2010)]

    # Clean NA values
    for col in ["residential", "commercial", "industrial", "total"]:
        df_old[col] = pd.to_numeric(df_old[col], errors="coerce").fillna(0)

    df_old = df_old[["year", "state", "residential", "commercial", "industrial", "total"]]

    # Combine
    out = pd.concat([df_old, df_new], ignore_index=True)
    out = out.sort_values(["year", "state"])
    out.to_csv(PUBLIC_DIR / "electricity-prices.csv", index=False)
    print(f"  Wrote {len(out)} rows to public/electricity-prices.csv")


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    download_all()
    process_generation()
    process_fuel_prices()
    process_electricity_prices()
    print("\nDone! Processed CSVs are in public/")
