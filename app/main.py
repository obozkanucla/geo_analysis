# app/main.py
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import json

# =============================
# 1. Sample Data
# =============================
combined_df = pd.DataFrame({
    "LAD25NM": ["City of London", "Liverpool", "Oxford", "Leeds"],
    "companies_per_1k": [5.2, 3.1, 4.0, 2.8]
})

st.set_page_config(page_title="UK Market Analysis", layout="wide")
st.title("🏴 UK Market Analysis (Interactive Map)")

st.subheader("Demand & Supply Data")
st.dataframe(combined_df)

# =============================
# 2. Load GeoJSON
# =============================
# geojson_path = "data/LAD_MAY_2025_UK_BGC_V2.geojson"
geojson_path = "/Users/obozkan/Library/Mobile Documents/com~apple~CloudDocs/__Python/geo_analysis/data/LAD_MAY_2025_UK_BGC_V2_1110015208521213948.geojson"
with open(geojson_path, "r") as f:
    geojson_data = json.load(f)

# =============================
# 3. Create Folium Map
# =============================
m = folium.Map(location=[54.5, -3], zoom_start=5)

# Add Choropleth directly
folium.Choropleth(
    geo_data=geojson_data,
    name="choropleth",
    data=combined_df,
    columns=["LAD25NM", "companies_per_1k"],
    key_on="feature.properties.LAD25NM",  # matches GeoJSON property
    fill_color="Reds",
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name="Companies per 1k target population"
).add_to(m)

# Add hover tooltip
for feature in geojson_data["features"]:
    lad_name = feature["properties"]["LAD25NM"]
    value = combined_df.loc[combined_df["LAD25NM"] == lad_name, "companies_per_1k"]
    val = float(value.values[0]) if not value.empty else 0
    folium.GeoJson(
        feature,
        tooltip=f"{lad_name}: {val:.2f}"
    ).add_to(m)

# Display map
st_folium(m, width=900, height=600)