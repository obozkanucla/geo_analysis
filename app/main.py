# app/main.py
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import json

# =============================
# 1. Sample Data
# =============================
lad_df = pd.DataFrame({
    "LAD25NM": ["City of London", "Liverpool", "Oxford", "Leeds"],
    "companies_per_1k": [5.2, 3.1, 4.0, 2.8]
})

city_df = pd.DataFrame({
    "City": ["London", "Manchester", "Birmingham", "Liverpool", "Leeds", "Sheffield", "Newcastle",
        "Bristol", "Glasgow", "Edinburgh"],
    "companies_per_1k": [5.2, 3.8, 4.1, 3.5, 2.8, 3.0, 2.6, 3.9, 4.3, 3.7]
})
region_df = pd.DataFrame({
    "Region": ["London", "North West", "South East", "Yorkshire and The Humber"],
    "companies_per_1k": [5.2, 3.1, 4.0, 2.8]
})

st.set_page_config(page_title="UK Market Analysis", layout="wide")
st.title("🏴 UK Market Analysis (Interactive Map)")

st.subheader("Demand & Supply Data")
level = st.radio(
    "Choose map level:",
    ("Regions", "Cities", "Local Authority Districts")
)

# =============================
# 2. Load GeoJSON
# =============================
# geojson_path = "data/LAD_MAY_2025_UK_BGC_V2.geojson"

if level == "Regions":
    geojson_path = "/Users/obozkan/Library/Mobile Documents/com~apple~CloudDocs/__Python/geo_analysis/data/Regions_December_2024_Boundaries_EN_BUC_4744747487989771477.geojson"
    df = region_df
    key_col = "Region"
    geojson_key = "feature.properties.RGN24NM"  # adjust to match geojson

elif level == "Cities":
    geojson_path = "data/cities.geojson"
    df = city_df
    key_col = "City"
    geojson_key = "feature.properties.City"

else:  # LADs
    geojson_path = "/Users/obozkan/Library/Mobile Documents/com~apple~CloudDocs/__Python/geo_analysis/data/LAD_MAY_2025_UK_BGC_V2_1110015208521213948.geojson"
    df = lad_df
    key_col = "LAD25NM"
    geojson_key = "feature.properties.LAD25NM"

st.dataframe(df)

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
    data=df,
    columns=[key_col, "companies_per_1k"],
    key_on=geojson_key,
    fill_color="Reds",
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name="Companies per 1k target population"
).add_to(m)

# Add hover tooltip
for feature in geojson_data["features"]:
    area_name = feature["properties"][key_col] if key_col in feature["properties"] else None
    if area_name:
        value = df.loc[df[key_col] == area_name, "companies_per_1k"]
        val = float(value.values[0]) if not value.empty else 0
        folium.GeoJson(
            feature,
            tooltip=f"{area_name}: {val:.2f}"
        ).add_to(m)


# Display map
st_folium(m, width=900, height=600)