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
from config import (CITIES_GEOJSON, LAD_GEOJSON, REGION_GEOJSON, COUNTY_GEOJSON,
                    LAD_POP_CSV, LAD_POP_CSV_AGG, LAD_TO_REGION_MAPPING, LAD_TO_COUNTY_MAPPING)
from analysis import load_lad_population


# =============================
# 2. Load GeoJSON & Prepare Data
# =============================
def aggregate_lad_to_level(lad_df, level_map, metric_col):
    """
    Aggregate LAD-level data to counties or regions based on a mapping dict.
    level_map: dict mapping LAD25NM -> County/Region
    """
    df = lad_df.copy()
    df[level_map['name']] = df['LAD23NM'].map(level_map['map'])
    agg_df = df.groupby(level_map['name'])[metric_col].mean().reset_index()
    agg_df.rename(columns={level_map['name']: level_map['name'], metric_col: metric_col}, inplace=True)
    return agg_df

# Function to aggregate LAD metrics to region
def aggregate_lad_to_region(lad_df, metric_col):
    """
    lad_df: DataFrame with LAD-level data
    metric_col: the column to aggregate (e.g., 'Total', 'over80_ratio')
    """
    df = lad_df.copy()
    df["Region"] = df["LAD23NM"].map(lad_region_dict)
    agg_df = df.groupby("Region")[metric_col].mean().reset_index()
    return agg_df

# Function to aggregate LAD metrics to region
def aggregate_lad_to_county(lad_df, metric_col):
    """
    lad_df: DataFrame with LAD-level data
    metric_col: the column to aggregate (e.g., 'Total', 'over80_ratio')
    """
    df = lad_df.copy()
    # --- Normalize LAD names to match the mapping keys ---
    df["LAD23NM"] = df["LAD23NM"].replace({
        "Herefordshire": "Herefordshire, County of",
        "Bristol": "Bristol, City of",
        "Kingston upon Hull": "Kingston upon Hull, City of"
    })

    df["County"] = df["LAD23NM"].map(lad_county_dict)

    # --- Handle special cases ---
    # Example: aggregate all Hertfordshire LADs into one value

    # """
    # herts_value = df.loc[df['LAD23NM'].str.contains("Hertfordshire"), metric_col].mean()  # or sum()
    # # Remove individual Hertfordshire LADs
    # df = df[~df['LAD23NM'].str.contains("Hertfordshire")]
    # # Add aggregated row
    # df = pd.concat([df, pd.DataFrame({"County": ["Hertfordshire"], metric_col: [herts_value]})], ignore_index=True)
    # """

    agg_df = df.groupby("County")[metric_col].mean().reset_index()
    return agg_df

# =============================
# 1. Sample Data
# =============================
# lad_df = pd.DataFrame({
#     "LAD25NM": ["City of London", "Liverpool", "Oxford", "Leeds"],
#     "companies_per_1k": [5.2, 3.1, 4.0, 2.8]
# })
# geojson_path = CITIES_GEOJSON
#
# # Load GeoJSON
# with open(geojson_path) as f:
#     geo = json.load(f)
#
# # Extract city names exactly as in GeoJSON
# city_names = [f["properties"]["TCITY15NM"] for f in geo["features"]]
#
# # Create DataFrame using these exact names
# city_df = pd.DataFrame({
#     "City": city_names,
#     "companies_per_1k": np.random.uniform(1, 6, len(city_names))  # demo values
# })
# region_df = pd.DataFrame({
#     "Region": ["London", "North West", "South East", "Yorkshire and The Humber"],
#     "companies_per_1k": [5.2, 3.1, 4.0, 2.8]
# })


# Load preprocessed data
# Streamlit page config
st.set_page_config(page_title="England & Wales Market Analysis", layout="wide")

# Load aggregated data at LAD level
lad_df = load_lad_population(LAD_POP_CSV_AGG)
# Load LAD-to-region mapping
lad_region_map = pd.read_csv(LAD_TO_REGION_MAPPING)  # your CSV path
lad_region_dict = dict(zip(lad_region_map["LAD23NM"], lad_region_map["RGN23NM"]))

lad_county_map = pd.read_csv(LAD_TO_COUNTY_MAPPING)  # your CSV path
lad_county_dict = dict(zip(lad_county_map["LTLA23NM"], lad_county_map["UTLA23NM"]))


# =============================
# 1. Select metric to map
# =============================
lad_metrics = [c for c in lad_df.columns if c != "LAD23NM"]  # exclude LAD name column
metric_col = st.selectbox("Choose metric to display on map:", lad_metrics)
legend_name = metric_col.replace("_", " ").title()

level = st.selectbox(
    "Choose map level:",
    ("Regions", "Counties", "Local Authority Districts") #"Cities" can be added separately
)

# =============================
# 1. Header & Dropdown
# =============================
st.markdown("<h2 style='margin-top:0; margin-bottom:0.2em;'>🏴 UK Market Analysis</h2>", unsafe_allow_html=True)
st.markdown("<h4 style='margin-top:0; margin-bottom:0.3em;'>Interactive Map</h4>", unsafe_allow_html=True)
st.subheader("Demand & Supply Data")

# =============================
# 2. Load GeoJSON
# =============================
# geojson_path = "data/LAD_MAY_2025_UK_BGC_V2.geojson"

if level == "Regions":
    geojson_path = REGION_GEOJSON
    df = aggregate_lad_to_region(lad_df, metric_col)
    # df = region_df
    key_col = "Region"
    geojson_key = "feature.properties.eer17nm"  # adjust to match geojson
    geojson_prop = "eer17nm"
    # metric_col = "companies_per_1k"
elif level == "Counties":
    geojson_path = COUNTY_GEOJSON
    # Create a placeholder counties dataframe (replace with real metrics)
    # counties = [f["properties"]["CTY24NM"] for f in json.load(open(geojson_path))["features"]]
    # df = pd.DataFrame({
    #     "County": counties,
    #     "companies_per_1k": np.random.uniform(1, 6, len(counties))
    # })eer17nm
    df = aggregate_lad_to_county(lad_df, metric_col)
    key_col = "County"
    geojson_key = "feature.properties.CTYUA23NM"
    geojson_prop = "CTYUA23NM"
    # metric_col = "companies_per_1k"

else:  # LADs
    geojson_path = LAD_GEOJSON
    df = lad_df.copy()  # use original LAD-level df
    df["LAD23NM"] = df["LAD23NM"].replace({
        "Herefordshire": "Herefordshire, County of",
        "Bristol": "Bristol, City of",
        "Kingston upon Hull": "Kingston upon Hull, City of"
    })
    # Make sure the column matches GeoJSON
    if "LAD23NM" in df.columns:
        df.rename(columns={"LAD23NM": "LAD25NM"}, inplace=True)
    key_col = "LAD25NM"
    geojson_key = "feature.properties.LAD25NM"
    geojson_prop = "LAD25NM"

with open(geojson_path, "r") as f:
    geojson_data = json.load(f)

if level == "Regions":
    for feature in geojson_data["features"]:
        if feature["properties"]["eer17nm"] == "Eastern":
            feature["properties"]["eer17nm"] = "East of England"
# elif level == "Counties":
#     # Normalize GeoJSON names
#     for feature in geojson_data["features"]:
#         name = feature["properties"]["CTYUA23NM"]
#         if name == "Bristol, City of":
#             feature["properties"]["CTYUA23NM"] = "Bristol"
#         elif name == "Kingston upon Hull, City of":
#             feature["properties"]["CTYUA23NM"] = "Kingston upon Hull"
#         elif name == "Herefordshire, County of":
#             feature["properties"]["CTYUA23NM"] = "Herefordshire"

    # print([f["properties"]["CTYUA23NM"] for f in geojson_data["features"]])
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
        columns=[key_col, metric_col],
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
            value = df.loc[df[key_col] == area_name, metric_col]
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