# app/mainMulti.py
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import json
import numpy as np
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))
from config import (
    CITIES_GEOJSON, LAD_GEOJSON, REGION_GEOJSON, COUNTY_GEOJSON,
    HOMECARE_AGENCIES_BY_LAD, LAD_POP_CSV_AGG,
    LAD_TO_REGION_MAPPING, LAD_TO_COUNTY_MAPPING
)
from analysis import load_lad_population

# =============================
# 0. Load Data
# =============================
st.set_page_config(page_title="England & Wales Market Analysis", layout="wide")

lad_df = load_lad_population(LAD_POP_CSV_AGG)
cqc_counts = pd.read_csv(HOMECARE_AGENCIES_BY_LAD)
lad_df = lad_df.merge(cqc_counts, left_on="LAD23NM", right_on="ladnm", how="left")
lad_df["num_agencies"] = lad_df["Agency_Count"].fillna(0)

# Age groups
age_groups = {
    "70plus": ["Aged 70 to 74 years", "Aged 75 to 79 years", "Aged 80 to 84 years", "Aged 85 years and over"],
    "75plus": ["Aged 75 to 79 years", "Aged 80 to 84 years", "Aged 85 years and over"],
    "80plus": ["Aged 80 to 84 years", "Aged 85 years and over"],
    "85plus": ["Aged 85 years and over"]
}
for group, cols in age_groups.items():
    lad_df[f"Population_{group}"] = lad_df[cols].sum(axis=1)
    lad_df[f"agencies_per_10k_{group}"] = (lad_df["num_agencies"] / lad_df[f"Population_{group}"] * 10000).fillna(0)

# LAD-to-region/county mapping
lad_region_dict = dict(zip(pd.read_csv(LAD_TO_REGION_MAPPING)["LAD23NM"],
                           pd.read_csv(LAD_TO_REGION_MAPPING)["RGN23NM"]))
lad_county_dict = dict(zip(pd.read_csv(LAD_TO_COUNTY_MAPPING)["LTLA23NM"],
                           pd.read_csv(LAD_TO_COUNTY_MAPPING)["UTLA23NM"]))

# =============================
# 1. Aggregation Functions
# =============================
def aggregate_lad(lad_df, metric_col, level="LAD"):
    if level == "Regions":
        df = lad_df.copy()
        df["Region"] = df["LAD23NM"].map(lad_region_dict)
        return df.groupby("Region")[metric_col].sum().reset_index()
    elif level == "Counties":
        df = lad_df.copy()
        df["LAD23NM"] = df["LAD23NM"].replace({
            "Herefordshire": "Herefordshire, County of",
            "Bristol": "Bristol, City of",
            "Kingston upon Hull": "Kingston upon Hull, City of"
        })
        df["County"] = df["LAD23NM"].map(lad_county_dict)
        return df.groupby("County")[metric_col].sum().reset_index()
    else:  # LADs
        df = lad_df.copy()
        df.rename(columns={"LAD23NM": "LAD25NM"}, inplace=True)
        return df[["LAD25NM", metric_col]]

# =============================
# 2. UI: Metric & Level Selection
# =============================
st.markdown("<h2>🏴 UK Market Analysis</h2>", unsafe_allow_html=True)
st.markdown("<h4>Interactive Map & Multi-Metrics</h4>", unsafe_allow_html=True)

lad_metrics = [c for c in lad_df.columns if c not in ["LAD23NM","ladnm","Agency_Count","num_agencies"]]
selected_metrics = st.multiselect("Choose metric(s) to display:", lad_metrics, default=lad_metrics[:1])
level = st.selectbox("Choose map level:", ("Regions", "Counties", "Local Authority Districts"))

# =============================
# 3. Load GeoJSON
# =============================
if level == "Regions":
    geojson_path = REGION_GEOJSON
    geojson_key = "feature.properties.eer17nm"
    key_col = "Region"
elif level == "Counties":
    geojson_path = COUNTY_GEOJSON
    geojson_key = "feature.properties.CTYUA23NM"
    key_col = "County"
else:
    geojson_path = LAD_GEOJSON
    geojson_key = "feature.properties.LAD25NM"
    key_col = "LAD25NM"

with open(geojson_path) as f:
    geojson_data = json.load(f)

# =============================
# 4. Map & Table
# =============================
col1, col2 = st.columns([2,1])

with col1:
    for metric in selected_metrics:
        st.markdown(f"**{metric.replace('_',' ').title()}**")
        df_map = aggregate_lad(lad_df, metric, level)

        m = folium.Map(location=[54.5, -3], zoom_start=5)
        folium.Choropleth(
            geo_data=geojson_data,
            name="choropleth",
            data=df_map,
            columns=[key_col, metric],
            key_on=geojson_key,
            fill_color="Reds",
            fill_opacity=0.7,
            line_opacity=0.2,
            legend_name=metric
        ).add_to(m)

        # Hover tooltip
        for feature in geojson_data["features"]:
            area_name = feature["properties"].get(key_col) or feature["properties"].get(key_col.replace("NM","nm"))
            if area_name:
                val = df_map.loc[df_map[key_col]==area_name, metric]
                val = float(val.values[0]) if not val.empty else 0
                folium.GeoJson(
                    feature,
                    style_function=lambda x: {'fillColor': 'transparent','color':'black','weight':0.5,'fillOpacity':0},
                    tooltip=f"{area_name}: {val:.2f}"
                ).add_to(m)
        st_folium(m, width=900, height=600)

with col2:
    st.subheader("📊 Top Values")
    for metric in selected_metrics:
        df_map = aggregate_lad(lad_df, metric, level)
        top5 = df_map[[key_col, metric]].sort_values(metric, ascending=False).head(5)
        st.markdown(f"**Top 5 {metric.replace('_',' ').title()}**")
        st.dataframe(top5)
        st.bar_chart(top5.set_index(key_col))