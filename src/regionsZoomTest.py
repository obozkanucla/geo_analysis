# app/main.py
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import json

# =============================
# 1. Sample Data
# =============================
region_df = pd.DataFrame({
    "Region": ["London", "North West", "South East", "Yorkshire and The Humber"],
    "companies_per_1k": [5.2, 3.1, 4.0, 2.8]
})

# =============================
# 2. Load GeoJSON
# =============================
geojson_path = "/Users/obozkan/Library/Mobile Documents/com~apple~CloudDocs/__Python/geo_analysis/data/Regions_December_2024_Boundaries_EN_BUC_4744747487989771477.geojson"
with open(geojson_path) as f:
    geojson_data = json.load(f)

# Precompute region centroids for zooming
centroids = {}
for feature in geojson_data["features"]:
    name = feature["properties"]["RGN24NM"]
    # approximate centroid from bounding box
    coords = feature["geometry"]["coordinates"]
    # handle MultiPolygon vs Polygon
    if feature["geometry"]["type"] == "MultiPolygon":
        all_coords = [pt for polygon in coords for ring in polygon for pt in ring]
    else:
        all_coords = [pt for ring in coords for pt in ring]
    lons, lats = zip(*all_coords)
    centroids[name] = [sum(lats)/len(lats), sum(lons)/len(lons)]

# =============================
# 3. Streamlit Layout
# =============================
st.set_page_config(page_title="UK Market Analysis", layout="wide")
st.title("🏴 UK Market Analysis (Regions)")

st.subheader("📊 Data Table")
selected_region = st.selectbox("Select Region to Zoom", region_df["Region"])

col1, col2 = st.columns([2, 1])

with col2:
    st.dataframe(region_df)

# Region selection

# =============================
# 4. Create Folium Map
# =============================
with col1:
    # Center map on selected region
    center = centroids[selected_region]
    m = folium.Map(location=center, zoom_start=7)  # set zoom here

    # Add choropleth for all regions
    folium.Choropleth(
        geo_data=geojson_data,
        name="choropleth",
        data=region_df,
        columns=["Region", "companies_per_1k"],
        key_on="feature.properties.RGN24NM",
        fill_color="Reds",
        fill_opacity=0.6,
        line_opacity=0.3,
        legend_name="Companies per 1k target population"
    ).add_to(m)

    # Highlight selected region
    for feature in geojson_data["features"]:
        name = feature["properties"]["RGN24NM"]
        folium.GeoJson(
            feature,
            style_function=lambda f, n=name: {
                "fillColor": "red" if n == selected_region else "transparent",
                "color": "black",
                "weight": 2,
                "fillOpacity": 0.5
            },
            tooltip=name
        ).add_to(m)

    st_folium(m, width=750, height=600)