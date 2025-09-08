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
from config import (CITIES_GEOJSON, LAD_GEOJSON, REGION_GEOJSON, COUNTY_GEOJSON, HOMECARE_AGENCIES_BY_LAD,
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
    agg_df = df.groupby(level_map['name'])[metric_col].sum().reset_index()

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
    # agg_df = df.groupby("Region")[metric_col].mean().reset_index()
    agg_df = df.groupby("Region")[metric_col].sum().reset_index()
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

    # agg_df = df.groupby("County")[metric_col].mean().reset_index()
    agg_df = df.groupby("County")[metric_col].sum().reset_index()

    return agg_df


def aggregate_lad_metrics(lad_df, level_map, level_name, population_cols, rating_cols, agency_col="num_agencies"):
    """
    Aggregate LAD-level data to counties or regions.

    Parameters
    ----------
    lad_df : pd.DataFrame
        LAD-level DataFrame containing populations, agencies, and CQC ratings
    level_map : dict
        Mapping from LAD name to higher level name (e.g., Region/County)
        Format: {"LAD23NM": "RegionName"}
    level_name : str
        Name of the aggregation level (e.g., "Region" or "County")
    population_cols : list
        List of population columns to sum (e.g., ['Population_70plus', 'Population_75plus'])
    rating_cols : list
        List of rating count columns (Good, Outstanding, Requires Improvement, Inadequate)
    agency_col : str
        Column name for total agencies (including rated and unrated)

    Returns
    -------
    agg_df : pd.DataFrame
        Aggregated DataFrame with:
            - summed populations
            - summed agency counts
            - summed CQC rating counts
            - recalculated agencies per 10k for age groups
            - CQC rating percentages
    """
    df = lad_df.copy()
    # print(df.columns)
    if level_name == "County":
        df["LAD23NM"] = df["LAD23NM"].replace({
        "Herefordshire": "Herefordshire, County of",
        "Bristol": "Bristol, City of",
        "Kingston upon Hull": "Kingston upon Hull, City of"
        })

    df[level_name] = df["LAD23NM"].map(level_map)

    # Columns to sum
    sum_cols = population_cols + [agency_col] + rating_cols + ["Not Rated"] + ['Total']

    # Aggregate by sum
    agg_df = df.groupby(level_name)[sum_cols].sum().reset_index()

    # Compute agencies per 10k for each age group
    for pop_col in population_cols:
        age_suffix = pop_col.split("_")[-1]  # e.g., '70plus'
        agg_df[f"agencies_per_10k_{age_suffix}"] = (agg_df[agency_col] / agg_df[pop_col]) * 10000
        agg_df[f"agencies_per_10k_{age_suffix}"] = agg_df[f"agencies_per_10k_{age_suffix}"].fillna(0)

    # Compute CQC rating percentages based on rated agencies only
    agg_df["Rated_Total"] = agg_df[rating_cols].sum(axis=1)
    for col in rating_cols:
        pct_col = f"{col}_pct"
        agg_df[pct_col] = (agg_df[col] / agg_df["Rated_Total"] * 100).fillna(0)

    # Compute Unrated percentage (of total agencies)
    agg_df["Unrated_pct"] = (agg_df["Not Rated"] / agg_df[agency_col] * 100).fillna(0)

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
# columns ['LAD23NM', 'Total', 'Aged 4 years and under', 'Aged 5 to 9 years',
#        'Aged 10 to 14 years', 'Aged 15 to 19 years', 'Aged 20 to 24 years',
#        'Aged 25 to 29 years', 'Aged 30 to 34 years', 'Aged 35 to 39 years',
#        'Aged 40 to 44 years', 'Aged 45 to 49 years', 'Aged 50 to 54 years',
#        'Aged 55 to 59 years', 'Aged 60 to 64 years', 'Aged 65 to 69 years',
#        'Aged 70 to 74 years', 'Aged 75 to 79 years', 'Aged 80 to 84 years',
#        'Aged 85 years and over', 'over80_ratio'
# print(lad_df.columns)

# Load CQC home care agency counts by LAD
cqc_counts = pd.read_csv(HOMECARE_AGENCIES_BY_LAD)  # columns: ladnm, Agency_Count
# print(cqc_counts.columns)

# Merge additional columns to the population stats
lad_df = lad_df.merge(cqc_counts, left_on="LAD23NM", right_on="ladnm", how="left")

# Fill LADs with no agencies with 0
lad_df["num_agencies"] = lad_df["Total_Agencies"].fillna(0)

# Optional: compute agencies per 10,000 people
# Define age group mappings with correct column names
age_groups = {
    "70plus": ["Aged 70 to 74 years", "Aged 75 to 79 years", "Aged 80 to 84 years", "Aged 85 years and over"],
    "75plus": ["Aged 75 to 79 years", "Aged 80 to 84 years", "Aged 85 years and over"],
    "80plus": ["Aged 80 to 84 years", "Aged 85 years and over"],
    "85plus": ["Aged 85 years and over"]
}
population_cols = ["Population_70plus", "Population_75plus", "Population_80plus", "Population_85plus"]
rating_cols = ["Good", "Outstanding", "Requires Improvement", "Inadequate"]

# Calculate Population Totals & LAD level stats

# Loop through each age group
for group_name, columns in age_groups.items():
    # Compute population for the age group
    lad_df[f"Population_{group_name}"] = lad_df[columns].sum(axis=1)

    # Compute agencies per 10,000 people in that age group
    lad_df[f"agencies_per_10k_{group_name}"] = (lad_df["num_agencies"] / lad_df[f"Population_{group_name}"]) * 10000

# Fill NaNs in case any LAD has zero population
lad_df[[f"agencies_per_10k_{g}" for g in age_groups.keys()]] = \
    lad_df[[f"agencies_per_10k_{g}" for g in age_groups.keys()]].fillna(0)


# Compute agencies per 10k for each age group
lad_df["agencies_per_10k_70"] = (lad_df["num_agencies"] / lad_df["Population_70plus"]) * 10000
lad_df["agencies_per_10k_75"] = (lad_df["num_agencies"] / lad_df["Population_75plus"]) * 10000
lad_df["agencies_per_10k_80"] = (lad_df["num_agencies"] / lad_df["Population_80plus"]) * 10000
lad_df["agencies_per_10k_85"] = (lad_df["num_agencies"] / lad_df["Population_85plus"]) * 10000

# Fill NaNs in case any LAD has zero population
lad_df[["agencies_per_10k_70","agencies_per_10k_75","agencies_per_10k_80","agencies_per_10k_85"]] = \
    lad_df[["agencies_per_10k_70","agencies_per_10k_75","agencies_per_10k_80","agencies_per_10k_85"]].fillna(0)


# Load LAD-to-region mapping
lad_region_map = pd.read_csv(LAD_TO_REGION_MAPPING)  # your CSV path
lad_region_dict = dict(zip(lad_region_map["LAD23NM"], lad_region_map["RGN23NM"]))

lad_county_map = pd.read_csv(LAD_TO_COUNTY_MAPPING)  # your CSV path
lad_county_dict = dict(zip(lad_county_map["LTLA23NM"], lad_county_map["UTLA23NM"]))

region_df = aggregate_lad_metrics(
    lad_df,
    level_map=lad_region_dict,
    level_name="Region",
    population_cols=population_cols,
    rating_cols=rating_cols,
    agency_col="num_agencies"
)

county_df = aggregate_lad_metrics(
    lad_df,
    level_map=lad_county_dict,
    level_name="County",
    population_cols=population_cols,
    rating_cols=rating_cols,
    agency_col="num_agencies"
)


# =============================
# 1. Select metric to map
# =============================
# metrics dict: old column -> new name
metric_dict = {
    "Total": "Total Population",
    "Population_70plus": "Population 70+",
    "Population_75plus": "Population 75+",
    "Population_80plus": "Population 80+",
    "Population_85plus": "Population 85+",
    "num_agencies": "Number of Homecare Agencies",
    "agencies_per_10k_70": "Agencies per 10k (70+)",
    "agencies_per_10k_75": "Agencies per 10k (75+)",
    "agencies_per_10k_80": "Agencies per 10k (80+)",
    "agencies_per_10k_85": "Agencies per 10k (85+)"
}

metric_dict.update({
    "Good": "Agencies Rated Good",
    "Outstanding": "Agencies Rated Outstanding",
    "Requires Improvement": "Agencies Requires Improvement",
    "Inadequate": "Agencies Rated Inadequate",
    "Not Rated": "Agencies Not Rated",
    "Good_pct": "% Agencies Good",
    "Outstanding_pct": "% Agencies Outstanding",
    "Requires Improvement_pct": "% Agencies Requires Improvement",
    "Inadequate_pct": "% Agencies Inadequate",
    "Unrated_pct": "% Agencies Not Rated"
})
# Clean metrics list for selection
clean_metrics = list(metric_dict.keys())
# Streamlit selectbox for a single metric
metric_col = st.selectbox(
    "Choose metric to display on map:",
    options=clean_metrics,
    format_func=lambda x: metric_dict[x],
    index=0  # first metric selected by default
)

lad_metrics = [c for c in lad_df.columns if c != "LAD23NM"]  # exclude LAD name column
# metric_col = st.selectbox("Choose metric to display on map:", lad_metrics)
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
    df = region_df
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
    df = county_df
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
        legend_name=metric_col
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