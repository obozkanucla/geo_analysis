# app/main.py
import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# Add project root
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.demand_loader import load_sample_demand
from src.supply_loader import load_sample_supply
from src.analysis import merge_demand_supply, compute_saturation
from src.geo_utils import load_shapefile, merge_geo_data, prepare_map_data

# =============================
# 1. Load Sample Data
# =============================
demand_df = load_sample_demand()
supply_df = load_sample_supply()
combined_df = merge_demand_supply(demand_df, supply_df)
combined_df = compute_saturation(combined_df)

# =============================
# 2. Streamlit Dashboard
# =============================
st.set_page_config(page_title="UK Market Analysis", layout="wide")
st.title("🏴 UK Market Analysis (Interactive Map)")

industry = st.selectbox(
    "Select Industry (SIC placeholder):",
    ["Home Care", "Fitness Gyms", "Restaurants"]
)
st.subheader(f"Demand & Supply Data — {industry}")
st.dataframe(combined_df)

# =============================
# 3. Interactive Map
# =============================
try:
    # Load shapefile (absolute path)
    gdf = load_shapefile(
        "/Users/obozkan/Library/Mobile Documents/com~apple~CloudDocs/"
        "__Python/geo_analysis/data/LAD_MAY_2025_UK_BGC_V2_2682909471764968542/"
        "LAD_MAY_2025_UK_BGC_V2.shp"
    )
    gdf = gdf.rename(columns={"LAD25NM": "region"})

    # Map high-level regions to LADs
    region_to_lads = {
        "London": ["City of London", "Barking and Dagenham", "Barnet", "Camden", "Croydon", "Ealing", "Enfield"],
        "North West": ["Halton", "Warrington", "Blackburn with Darwen", "Blackpool", "Liverpool", "Manchester"],
        "South East": ["Kent", "Brighton and Hove", "Medway", "Reading", "Oxford", "Milton Keynes"],
        "Yorkshire": ["Leeds", "York", "East Riding of Yorkshire", "Bradford", "Sheffield", "Hull"]
    }

    rows = []
    for high_region, lads in region_to_lads.items():
        for lad in lads:
            rows.append({"region_lad": lad, "parent_region": high_region})
    region_map_df = pd.DataFrame(rows)

    combined_expanded = combined_df.merge(
        region_map_df,
        left_on="region",
        right_on="parent_region"
    )

    # Merge shapefile with sample data
    map_df = merge_geo_data(gdf, combined_expanded, geodf_key="region", df_key="region_lad")
    map_df = prepare_map_data(map_df, "companies_per_1k")

    # Create Folium map
    m = folium.Map(location=[54.5, -3], zoom_start=5)
    folium.Choropleth(
        geo_data=map_df,
        data=map_df,
        columns=["region", "companies_per_1k"],
        key_on="feature.properties.region",
        fill_color="Reds",
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name="Companies per 1k target population"
    ).add_to(m)

    # Add hover tooltip
    for _, row in map_df.iterrows():
        folium.GeoJson(
            row["geometry"],
            tooltip=f"{row['region']}: {row['companies_per_1k']:.2f}"
        ).add_to(m)

    st_folium(m, width=900, height=600)

except Exception as e:
    st.warning(f"Map could not be loaded: {e}")