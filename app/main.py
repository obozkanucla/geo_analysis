# app/main.py
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import json
import numpy as np

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))
from config import CITIES_GEOJSON, LAD_GEOJSON, REGION_GEOJSON, COUNTY_GEOJSON, LAD_POP_CSV
# =============================
# 1. Sample Data
# =============================
lad_df = pd.DataFrame({
    "LAD25NM": ["City of London", "Liverpool", "Oxford", "Leeds"],
    "companies_per_1k": [5.2, 3.1, 4.0, 2.8]
})

geojson_path = CITIES_GEOJSON

# Load GeoJSON
with open(geojson_path) as f:
    geo = json.load(f)

# Extract city names exactly as in GeoJSON
city_names = [f["properties"]["TCITY15NM"] for f in geo["features"]]

# Create DataFrame using these exact names
city_df = pd.DataFrame({
    "City": city_names,
    "companies_per_1k": np.random.uniform(1, 6, len(city_names))  # demo values
})

region_df = pd.DataFrame({
    "Region": ["London", "North West", "South East", "Yorkshire and The Humber"],
    "companies_per_1k": [5.2, 3.1, 4.0, 2.8]
})

# Streamlit page config
st.set_page_config(page_title="UK Market Analysis", layout="wide")
# =============================
# 1. Header & Dropdown
# =============================
st.markdown("<h2 style='margin-top:0; margin-bottom:0.2em;'>🏴 UK Market Analysis</h2>", unsafe_allow_html=True)
st.markdown("<h4 style='margin-top:0; margin-bottom:0.3em;'>Interactive Map</h4>", unsafe_allow_html=True)

st.subheader("Demand & Supply Data")
level = st.selectbox(
    "Choose map level:",
    ("Regions", "Counties", "Local Authority Districts") #"Cities", c
)

# =============================
# 2. Load GeoJSON
# =============================
# geojson_path = "data/LAD_MAY_2025_UK_BGC_V2.geojson"

if level == "Regions":
    geojson_path = REGION_GEOJSON
    df = region_df
    key_col = "Region"
    geojson_key = "feature.properties.RGN24NM"  # adjust to match geojson
    geojson_prop = "RGN24NM"

elif level == "Counties":
    geojson_path = COUNTY_GEOJSON
    # Create a placeholder counties dataframe (replace with real metrics)
    counties = [f["properties"]["CTY24NM"] for f in json.load(open(geojson_path))["features"]]
    df = pd.DataFrame({
        "County": counties,
        "companies_per_1k": np.random.uniform(1, 6, len(counties))
    })
    key_col = "County"
    geojson_key = "feature.properties.CTY24NM"
    geojson_prop = "CTY24NM"

elif level == "Cities":
    geojson_path = CITIES_GEOJSON
    df = city_df
    key_col = "City"
    geojson_key = "feature.properties.TCITY15NM"
    geojson_prop = "TCITY15NM"

else:  # LADs
    geojson_path = LAD_GEOJSON
    df = lad_df
    key_col = "LAD25NM"
    geojson_key = "feature.properties.LAD25NM"
    geojson_prop = "LAD25NM"

with open(geojson_path, "r") as f:
    geojson_data = json.load(f)

# =================================
# 3. Create Folium Map & Data Table
# =================================
col1, col2 = st.columns([2, 1])  # map gets more space than table
with col1:

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
        area_name = feature["properties"].get(geojson_prop) if geojson_prop in feature["properties"] else None
        # area_name = feature["properties"][key_col] if key_col in feature["properties"] else None
        # print(area_name)
        if area_name:
            value = df.loc[df[key_col] == area_name, "companies_per_1k"]
            val = float(value.values[0]) if not value.empty else 0
            folium.GeoJson(
                feature,
                style_function=lambda x: {
                    'fillColor': 'transparent',
                    'color': 'black',  # or transparent
                    'weight': 0.5,  # thin border
                    'fillOpacity': 0
                },
                tooltip=f"{area_name}: {val:.2f}"
            ).add_to(m)

    # Display map
    st_folium(m, width=900, height=750)

with col2:
    st.subheader("📊 Data Table")
    st.dataframe(df)