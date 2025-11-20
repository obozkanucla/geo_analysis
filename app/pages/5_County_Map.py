import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from pathlib import Path
import json
import re
from operator_mapping import (
    map_franchise_row,
    map_corporate_group,
    classify_operator
)
# ============================================================
# 🔧 PATHS (relative)
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

DATA_PATH = ROOT / "data" / "HomeCareAgencies_data (08-09-2025)(ALL_CQC_RATINGS)_postcodes.csv"
ONSPD_PATH = ROOT / "data" / "postcode_centroids_small.csv" #
LAD_TO_COUNTY = ROOT / "data" / \
    "Local_Authority_District_to_County_and_Unitary_Authority_(April_2023)_Lookup_in_EW.csv"
COUNTY_GEOJSON = ROOT / "data" / \
    "Counties_and_Unitary_Authorities_December_2023_Boundaries_UK_BSC_4952317392296043005.geojson"

# ============================================================
# 🧬 MARKET STRUCTURE (original logic)
# ============================================================

group_mapping = {
    "Cera Care": [
        "Cera Care", "Cera Homecare", "Cera Care Carers", "Cera Care Central",
        "Cera Care Germany", "Cera Care Operations", "Cera Care Technology",
        "Apex Prime Care", "Apex Prime Care Holdings", "Apex Prime Care Group",
        "Mediline Home Care", "Nobilis Care", "Premier Care", "Velvet Glove Care",
        "Cardiff Homecare", "Homecare4U", "Alpenbest", "Care Quality Services",
        "Allied Health Support", "Gemcare South West", "BruDi Homecare"
    ],
    "Helping Hands": ["Midshires Care Limited", "Helping Hands"],
    "McCarthy & Stone": ["Yourlife Management Services Limited", "McCarthy & Stone"],
    "Radis Group": ["G P Homecare Limited", "Radis Community Care"],
    "Housing 21": ["Housing 21"],
    "Creative Support": ["Creative Support Limited", "Creative Support"],
    "Achieve Together": ["Achieve Together Limited", "Achieve Together"],
    "Mencap": ["Royal Mencap Society", "Mencap"],
    "Voyage Care": ["Voyage 1 Limited", "Voyage Care"],
    "Care Outlook": ["Care Outlook Ltd", "Care Outlook"],
}

franchise_mapping = {
    "Home Instead": "Home Instead",
    "Bluebird Care": "Bluebird Care",
    "Caremark": "Caremark",
    "Right At Home": "Right At Home",
    "Kare Plus": "Kare Plus",
    "Radfield": "Radfield Home Care",
    "Walfinch": "Walfinch",
    "PerCurra": "PerCurra",
    "Hallows": "Hallows Care",
    "Good Oaks": "Good Oaks Home Care",
    "Prestige": "Prestige Nursing & Care",
    "Everycare": "Everycare",
    "ComForcare": "ComForcare",
    "Extra Help": "Extra Help",
    "Avant Healthcare": "Avant Healthcare",
    "Seniors Helping Seniors": "Seniors Helping Seniors",
    "Apollo Care": "Apollo Care",
    "Heritage": "Heritage Healthcare",
    "Sylvian": "SylvianCare",
    "Blossom": "Blossom Home Care",
    "Nurse Next Door": "Nurse Next Door",
    "Homewatch": "Homewatch CareGivers",
    "Interim Healthcare": "Interim Healthcare",
    "Lastminute Care": "Lastminute Care & Nursing",
}

true_franchises = list(franchise_mapping.values())


def clean_name(name):
    if not isinstance(name, str):
        return ""
    name = re.sub(r"[–—−]", "-", name)
    name = " ".join(name.split())
    name = re.sub(r"[^\w\s-]", "", name)
    return name.lower().strip()


def map_franchise(name):
    c = clean_name(name)
    if "home instead" in c:
        return "Home Instead"
    for k, brand in franchise_mapping.items():
        if clean_name(k) in c:
            return brand
    return None


def map_corporate_group(name):
    n = str(name).lower()
    for parent, subs in group_mapping.items():
        for s in subs:
            if s.lower() in n:
                return parent
    return None


def classify_operator(row):
    if row.get("Franchise") in true_franchises:
        return "Franchise group"
    if row.get("num_agencies", 0) > 1:
        return "Multi-location operator (non-franchise)"
    return "Independent small"


# ============================================================
# 📥 Load Data
# ============================================================

st.set_page_config(page_title="5-County Operator Map", layout="wide")

st.header("🏥 Homecare Market Structure — County View")

df = pd.read_csv(DATA_PATH)
df["Provider name"] = df["Provider name"].astype(str).str.strip().str.title()

# ============================================================
# 📍 LAD → County mapping
# ============================================================

lad_map = pd.read_csv(LAD_TO_COUNTY)
lad_map = lad_map[["LTLA23NM", "UTLA23NM"]].drop_duplicates()

lad_map["LTLA23NM"] = lad_map["LTLA23NM"].str.strip()
lad_map["UTLA23NM"] = lad_map["UTLA23NM"].str.strip()

df["ladnm"] = df["ladnm"].astype(str).str.strip()

df = df.merge(
    lad_map,
    left_on="ladnm",
    right_on="LTLA23NM",
    how="left"
)

df.rename(columns={"UTLA23NM": "County_clean"}, inplace=True)
df = df.dropna(subset=["County_clean"])

# ============================================================
# 📍 Coordinates via ONSPD (Postcode-based)
# ============================================================

centroids = pd.read_csv(ONSPD_PATH, usecols=["PCDS", "LAT", "LONG"])
centroids["PCDS_clean"] = centroids["PCDS"].str.replace(" ", "").str.upper()

df["pcds_clean"] = (
    df["Postcode"]
    .astype(str)
    .str.replace(" ", "")
    .str.upper()
)

df = df.merge(
    centroids[["PCDS_clean", "LAT", "LONG"]],
    left_on="pcds_clean",
    right_on="PCDS_clean",
    how="left"
)

df = df.dropna(subset=["LAT", "LONG"])

# ============================================================
# 🧬 Operator model (franchise/corporate)
# ============================================================

df["Franchise"] = df.apply(map_franchise_row, axis=1)
df["CorporateGroup"] = df["Provider name"].apply(map_corporate_group)

df["MarketEntity"] = (
    df["Franchise"]
      .combine_first(df["CorporateGroup"])
      .combine_first(df["Provider name"])
)

counts = df.groupby("MarketEntity").size().reset_index(name="num_agencies")
df = df.merge(counts, on="MarketEntity", how="left")

df["OperatorType"] = df.apply(classify_operator, axis=1)

sorted_entities = df.groupby("MarketEntity")["Provider name"].count().sort_values(ascending=False)
TOP10 = set(sorted_entities.head(10).index)
TOP20 = set(sorted_entities.head(20).index)

df["Top10"] = df["MarketEntity"].isin(TOP10)
df["Top20"] = df["MarketEntity"].isin(TOP20)

# ============================================================
# 🎛 SIDEBAR CONTROLS
# ============================================================

st.sidebar.header("Filters")

counties_available = sorted(df["County_clean"].unique())

selected_counties = st.sidebar.multiselect(
    "Select counties:",
    counties_available,
    default=[]
)

operator_types = st.sidebar.multiselect(
    "Operator types:",
    ["Franchise group", "Multi-location operator (non-franchise)", "Independent small"],
    default=[]
)

top_filter = st.sidebar.selectbox(
    "Top operators:",
    ["All", "Top 10", "Top 20"]
)

# ============================================================
# 🧼 Apply filters
# ============================================================

filtered = df.copy()

if selected_counties:
    filtered = filtered[filtered["County_clean"].isin(selected_counties)]

if operator_types:
    filtered = filtered[filtered["OperatorType"].isin(operator_types)]

if top_filter == "Top 10":
    filtered = filtered[filtered["Top10"]]
elif top_filter == "Top 20":
    filtered = filtered[filtered["Top20"]]

st.success(f"Found **{len(filtered)}** agencies in selected filters.")

# ==========================================================
# MARKET ENTITY MAPPING (insert block HERE)
# ==========================================================

df["Franchise"] = df["Provider name"].apply(map_franchise)
df["CorporateGroup"] = df["Provider name"].apply(map_corporate_group)

df["MarketEntity"] = (
    df["Franchise"]
      .combine_first(df["CorporateGroup"])
      .combine_first(df["Provider name"])
)

# Count agencies per market entity
entity_counts = (
    df.groupby("MarketEntity")
      .size()
      .reset_index(name="num_agencies")
)
df = df.merge(entity_counts, on="MarketEntity", how="left")

df["OperatorType"] = df.apply(classify_operator, axis=1)

df["OperatorType"] = df.apply(classify_operator, axis=1)

# ============================================================
# 🗺 MAP RENDERING
# ============================================================

with open(COUNTY_GEOJSON, "r") as f:
    geojson = json.load(f)

if len(filtered) > 0:
    avg_lat = filtered["LAT"].mean()
    avg_lon = filtered["LONG"].mean()
else:
    avg_lat, avg_lon = (54.5, -3)

m = folium.Map(location=[avg_lat, avg_lon], zoom_start=8)

# Highlight selected counties
def county_style(feature):
    cname = feature["properties"].get("UTLA23NM")
    if selected_counties and cname in selected_counties:
        return {"fillColor": "#ffcc99", "color": "black", "weight": 2, "fillOpacity": 0.5}
    return {"fillColor": "transparent", "color": "gray", "weight": 1, "fillOpacity": 0}

folium.GeoJson(
    geojson,
    name="Counties",
    style_function=county_style
).add_to(m)

# Plot agencies
for _, row in filtered.iterrows():
    colour = "blue" if row["Top10"] else "green" if row["Franchise"] else "gray"

    folium.CircleMarker(
        location=[row["LAT"], row["LONG"]],
        radius=4,
        color=colour,
        fill=True,
        fill_opacity=0.8,
        popup=f"<b>{row['Provider name']}</b><br>{row['MarketEntity']}<br>{row['County_clean']}",
    ).add_to(m)

st_folium(m, height=800, width=None)

# ============================================================
# 📄 Data Table + Download
# ============================================================

st.subheader("📋 Filtered Agencies")
st.dataframe(filtered)

st.download_button(
    "⬇ Download filtered agencies (CSV)",
    filtered.to_csv(index=False),
    file_name="filtered_agencies.csv",
    mime="text/csv"
)