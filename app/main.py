import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import json
import numpy as np
import os
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))
from config import (
    CITIES_GEOJSON, LAD_GEOJSON, REGION_GEOJSON, COUNTY_GEOJSON,
    HOMECARE_AGENCIES_BY_LAD, LAD_POP_CSV, LAD_POP_CSV_AGG,
    LAD_TO_REGION_MAPPING, LAD_TO_COUNTY_MAPPING, BASE_DIR
)
from analysis import load_lad_population


# =============================
# Helper: Cached Geocoder with Persistent CSV
# =============================
@st.cache_data
def geocode_postcodes(df, postcode_col="Postcode", cache_file=f"{BASE_DIR}/geocoded_agencies.csv"):
    """
    Geocode postcodes using OpenStreetMap (Nominatim) with caching to CSV.
    On re-runs, only new postcodes are looked up.
    """
    from geopy.geocoders import Nominatim
    from geopy.extra.rate_limiter import RateLimiter

    df = df.copy()

    # Load cached geocodes if available
    if os.path.exists(cache_file):
        cached = pd.read_csv(cache_file)
        st.info(f"📂 Loaded {len(cached)} cached postcodes from {os.path.basename(cache_file)}")
    else:
        cached = pd.DataFrame(columns=[postcode_col, "Latitude", "Longitude"])

    # Find which postcodes need geocoding
    missing = df[~df[postcode_col].isin(cached[postcode_col])]
    if len(missing) > 0:
        st.info(f"⏳ Geocoding {len(missing)} new postcodes (cached results will be reused)...")
        geolocator = Nominatim(user_agent="geo_analysis_app")
        geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

        new_rows = []
        progress = st.progress(0)
        for i, code in enumerate(missing[postcode_col].dropna().unique()):
            loc = geocode(code)
            if loc:
                new_rows.append({
                    postcode_col: code,
                    "Latitude": loc.latitude,
                    "Longitude": loc.longitude
                })
            progress.progress((i + 1) / len(missing))

        if new_rows:
            new_df = pd.DataFrame(new_rows)
            cached = pd.concat([cached, new_df], ignore_index=True)
            cached.to_csv(cache_file, index=False)
            st.success(f"💾 Saved {len(new_rows)} new geocoded postcodes to {cache_file}")
    else:
        st.success("✅ All postcodes already geocoded and cached.")

    df = df.merge(cached, on=postcode_col, how="left")
    return df.dropna(subset=["Latitude", "Longitude"])


# =============================
# Aggregation Functions
# =============================
def aggregate_lad_to_level(lad_df, level_map, metric_col):
    df = lad_df.copy()
    df[level_map['name']] = df['LAD23NM'].map(level_map['map'])
    agg_df = df.groupby(level_map['name'])[metric_col].sum().reset_index()
    return agg_df


def aggregate_lad_metrics(lad_df, level_map, level_name, population_cols, rating_cols, agency_col="num_agencies"):
    df = lad_df.copy()
    if level_name == "County":
        df["LAD23NM"] = df["LAD23NM"].replace({
            "Herefordshire": "Herefordshire, County of",
            "Bristol": "Bristol, City of",
            "Kingston upon Hull": "Kingston upon Hull, City of"
        })

    df[level_name] = df["LAD23NM"].map(level_map)
    sum_cols = population_cols + [agency_col] + rating_cols + ["Not Rated"] + ["Total"]
    agg_df = df.groupby(level_name)[sum_cols].sum().reset_index()

    for pop_col in population_cols:
        suffix = pop_col.split("_")[-1]
        agg_df[f"agencies_per_10k_{suffix}"] = (agg_df[agency_col] / agg_df[pop_col]) * 10000
        agg_df[f"agencies_per_10k_{suffix}"] = agg_df[f"agencies_per_10k_{suffix}"].fillna(0)

    agg_df["Rated_Total"] = agg_df[rating_cols].sum(axis=1)
    for col in rating_cols:
        agg_df[f"{col}_pct"] = (agg_df[col] / agg_df["Rated_Total"] * 100).fillna(0)
    agg_df["Unrated_pct"] = (agg_df["Not Rated"] / agg_df[agency_col] * 100).fillna(0)
    return agg_df


# =============================
# Streamlit Config
# =============================
st.set_page_config(page_title="England & Wales Market Analysis", layout="wide")
st.markdown("<h2 style='margin-top:0;'>🏴 UK Homecare Market Analysis</h2>", unsafe_allow_html=True)


# =============================
# Load Data
# =============================
lad_df = load_lad_population(LAD_POP_CSV_AGG)
cqc_counts = pd.read_csv(HOMECARE_AGENCIES_BY_LAD)
lad_df = lad_df.merge(cqc_counts, left_on="LAD23NM", right_on="ladnm", how="left")
lad_df["num_agencies"] = lad_df["Total_Agencies"].fillna(0)

# Age group populations
age_groups = {
    "70plus": ["Aged 70 to 74 years", "Aged 75 to 79 years", "Aged 80 to 84 years", "Aged 85 years and over"],
    "75plus": ["Aged 75 to 79 years", "Aged 80 to 84 years", "Aged 85 years and over"],
    "80plus": ["Aged 80 to 84 years", "Aged 85 years and over"],
    "85plus": ["Aged 85 years and over"]
}
population_cols = ["Population_70plus", "Population_75plus", "Population_80plus", "Population_85plus"]
rating_cols = ["Good", "Outstanding", "Requires Improvement", "Inadequate"]

for group, cols in age_groups.items():
    lad_df[f"Population_{group}"] = lad_df[cols].sum(axis=1)
    lad_df[f"agencies_per_10k_{group}"] = (lad_df["num_agencies"] / lad_df[f"Population_{group}"]) * 10000
    lad_df[f"agencies_per_10k_{group}"] = lad_df[f"agencies_per_10k_{group}"].fillna(0)

# Region/County mapping
lad_region_map = pd.read_csv(LAD_TO_REGION_MAPPING)
lad_county_map = pd.read_csv(LAD_TO_COUNTY_MAPPING)
lad_region_dict = dict(zip(lad_region_map["LAD23NM"], lad_region_map["RGN23NM"]))
lad_county_dict = dict(zip(lad_county_map["LTLA23NM"], lad_county_map["UTLA23NM"]))

region_df = aggregate_lad_metrics(lad_df, lad_region_dict, "Region", population_cols, rating_cols)
county_df = aggregate_lad_metrics(lad_df, lad_county_dict, "County", population_cols, rating_cols)


# =============================
# Load and Geocode Agency Data
# =============================
# try:
#     agencies_df = pd.read_csv(HOMECARE_AGENCIES_BY_LAD.replace("_LAD_CQC_counts", ""))
#     if "Postcode" in agencies_df.columns:
#         agencies_df = geocode_postcodes(
#             agencies_df,
#             postcode_col="Postcode",
#             cache_file=f"{BASE_DIR}/geocoded_agencies.csv"
#         )
#     else:
#         st.warning("⚠️ No 'Location_Postcode' column found in agency dataset.")
#         agencies_df = pd.DataFrame()
# except Exception as e:
#     st.error(f"Could not load agency data: {e}")
#     agencies_df = pd.DataFrame()


# =============================
# Load and merge Agency Data with ONSPD Centroids
# =============================
from config import HOMECARE_AGENCIES, BASE_DIR

try:
    # Load detailed agency dataset
    agencies_df = pd.read_csv(HOMECARE_AGENCIES)
    agencies_df["Postcode"] = agencies_df["Postcode"].str.strip().str.upper()

    # Load pre-trimmed ONSPD centroids (from your 150MB file)
    onspd_path = f"{BASE_DIR}/ONSPD_Centroids.csv"
    if os.path.exists(onspd_path):
        st.info("📍 Using local ONSPD centroid lookup for postcodes...")
        centroids = pd.read_csv(onspd_path, usecols=["PCDS", "LAT", "LONG"])
        centroids["PCDS"] = centroids["PCDS"].str.strip().str.upper()

        # Merge agencies with postcode coordinates
        agencies_df = agencies_df.merge(
            centroids,
            left_on="Postcode",
            right_on="PCDS",
            how="left"
        )
        agencies_df = agencies_df.dropna(subset=["LAT", "LONG"])
        agencies_df.rename(columns={"LAT": "Latitude", "LONG": "Longitude"}, inplace=True)

        st.success(f"✅ Mapped {len(agencies_df)} agencies to coordinates.")



        # =============================
        # Count companies with >5 branches
        # =============================
        # if not agencies_df.empty and "Provider name" in agencies_df.columns:
        #     branch_counts = agencies_df["Provider name"].value_counts()
        #     large_providers = branch_counts[branch_counts > 5]
        #     st.write(f"🏢 There are **{len(large_providers)}** providers with more than 5 branches.")
        #     st.dataframe(large_providers.rename("Branch count"))
        # else:
        #     st.warning("⚠️ Provider name column not found or agency dataset is empty.")

        # =============================
        # Filter for geography: south of Birmingham
        # =============================
        # BIRMINGHAM_LAT = 52.48
        #
        # # Filter to only those agencies south of Birmingham
        # agencies_south = agencies_df[agencies_df["Latitude"] < BIRMINGHAM_LAT].copy()
        #
        # # Count branches per provider (south only)
        # south_branch_counts = agencies_south["Provider name"].value_counts()
        # south_large = south_branch_counts[south_branch_counts > 5]
        #
        # st.write(f"📍 There are **{len(south_large)}** providers with more than 5 branches south of Birmingham.")
        # st.dataframe(south_large.rename('Branch count (south of Birmingham)'))

    else:
        st.error("❌ ONSPD_Centroids.csv not found. Please run trim_onspd.py first.")
        agencies_df = pd.DataFrame()

except Exception as e:
    st.error(f"❌ Could not load or merge agency data: {e}")
    agencies_df = pd.DataFrame()

# =============================
# Metric & Level Selection
# =============================
metric_dict = {
    "Total": "Total Population",
    "Population_70plus": "Population 70+",
    "Population_75plus": "Population 75+",
    "Population_80plus": "Population 80+",
    "Population_85plus": "Population 85+",
    "num_agencies": "Number of Homecare Agencies",
    "agencies_per_10k_70plus": "Agencies per 10k (70+)",
    "agencies_per_10k_75plus": "Agencies per 10k (75+)",
    "agencies_per_10k_80plus": "Agencies per 10k (80+)",
    "agencies_per_10k_85plus": "Agencies per 10k (85+)"
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

metric_col = st.selectbox(
    "Choose metric to display on map:",
    options=list(metric_dict.keys()),
    format_func=lambda x: metric_dict[x],
    index=0
)

level = st.selectbox(
    "Choose map level:",
    ("Regions", "Counties", "Local Authority Districts")
)


# =============================
# Create Geo Map
# =============================
if level == "Regions":
    geojson_path = REGION_GEOJSON
    df, key_col, geojson_prop = region_df, "Region", "eer17nm"
elif level == "Counties":
    geojson_path = COUNTY_GEOJSON
    df, key_col, geojson_prop = county_df, "County", "CTYUA23NM"
else:
    geojson_path = LAD_GEOJSON
    df, key_col, geojson_prop = lad_df.copy(), "LAD23NM", "LAD25NM"
    key_col = "LAD25NM"          # <- changed here
    geojson_prop = "LAD25NM"
    df["LAD23NM"] = df["LAD23NM"].replace({
        "Herefordshire": "Herefordshire, County of",
        "Bristol": "Bristol, City of",
        "Kingston upon Hull": "Kingston upon Hull, City of"
    })
    df.rename(columns={"LAD23NM": "LAD25NM"}, inplace=True)

with open(geojson_path, "r") as f:
    geojson_data = json.load(f)

# Map + Choropleth
m = folium.Map(location=[54.5, -3], zoom_start=5)
folium.Choropleth(
    geo_data=geojson_data,
    name=None,
    data=df,
    columns=[key_col, metric_col],
    key_on=f"feature.properties.{geojson_prop}",
    fill_color="Reds",
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name=metric_col
).add_to(m)

# =============================
# Agency Markers (only for LAD)
# =============================
if level == "Local Authority Districts" and not agencies_df.empty:
    from folium.plugins import MarkerCluster

    st.markdown("#### 🏥 Homecare Agency Locations")
    agencies_filtered = agencies_df.dropna(subset=["Latitude", "Longitude"])

    # Explicit provider column
    provider_col = "Provider name"
    # Detect rating column (case-insensitive)
    rating_col = next((c for c in agencies_filtered.columns if "rating" in c.lower()), None)
    # Map of rating short codes
    rating_map = {
        "Outstanding": "O",
        "Good": "G",
        "Requires improvement": "RI",
        "Requires Improvement": "RI",
        "Inadequate": "I",
        "Not yet rated": "N/A",
        "Not Rated": "N/A",
        "N/A": "N/A"
    }
    # Compute counts per provider
    provider_summary = []
    for prov, group in agencies_filtered.groupby(provider_col):
        total = len(group)
        if total < 5:
            continue  # skip small ones

        # Count each rating type
        rating_counts = group[rating_col].fillna("N/A").map(rating_map).value_counts().to_dict()
        summary = {
            "Provider": prov,
            "Total": total,
            "O": rating_counts.get("O", 0),
            "G": rating_counts.get("G", 0),
            "RI": rating_counts.get("RI", 0),
            "I": rating_counts.get("I", 0),
            "N/A": rating_counts.get("N/A", 0),
        }
        provider_summary.append(summary)

    provider_counts = agencies_filtered["Provider name"].value_counts()
    # large_providers = provider_counts[provider_counts >= 5].index
    large_providers = provider_counts[provider_counts >= 5].sort_values(ascending=False)
    # print(large_providers)
    # Build dropdown labels with counts
    # provider_options = ["All"] + [
    #     f"{prov} ({count})" for prov, count in large_providers.items()
    # ]
    # Build dropdown labels
    provider_options = ["All"] + [
        f"{p['Provider']} (total={p['Total']}, O={p['O']}, G={p['G']}, RI={p['RI']}, I={p['I']}, N/A={p['N/A']})"
        for p in sorted(provider_summary, key=lambda x: x['Total'], reverse=True)
    ]

    selected_option = st.selectbox(
        "Select provider (≥5 locations):",
        options=list(provider_options),
        index=0
    )
    # Parse provider name back from label
    if selected_option != "All":
        selected_provider = selected_option.split(" (")[0]
        # print(selected_provider)
        agencies_filtered = agencies_filtered[agencies_filtered["Provider name"] == selected_provider]
    else:
        selected_provider = None

    # selected_provider = st.selectbox(
    #     "Select provider (≥5 locations):",
    #     options=["All"] + list(large_providers),
    #     index=0
    # )

    # if selected_provider != "All":
    #     agencies_filtered = agencies_filtered[agencies_filtered["Provider name"] == selected_provider]

    marker_cluster = MarkerCluster(name="Homecare Agencies").add_to(m)

    # for _, row in agencies_filtered.iterrows():
    #     popup_html = f"<b>{row['Provider name']}</b><br>{row.get('Location_Name', '')}<br>{row.get('Postcode', '')}"
    #     folium.CircleMarker(
    #         location=[row["Latitude"], row["Longitude"]],
    #         radius=4,
    #         color="blue",
    #         fill=True,
    #         fill_opacity=0.7,
    #         popup=popup_html,
    #         tooltip=row.get("Location_Name", row["Provider name"])
    #     ).add_to(marker_cluster)
    # Define color mapping for CQC ratings
    rating_col = next((c for c in agencies_filtered.columns if "rating" in c.lower()), None)
    rating_colors = {
        "Outstanding": "darkgreen",
        "Good": "green",
        "Requires improvement": "orange",
        "Inadequate": "red",
        "Not yet rated": "gray",
        "Not Rated": "gray",
        "N/A": "gray",
        None: "gray",
        np.nan: "gray"
    }

    # =============================
    # 🎯 Filter by CQC Rating
    # =============================
    rating_options = ["All", "Outstanding", "Good", "Requires improvement", "Inadequate", "Not yet rated"]
    rating_filter = st.selectbox("Filter by CQC Rating:", options=rating_options, index=0)

    if rating_filter != "All":
        agencies_filtered = agencies_filtered[
            agencies_filtered[rating_col].str.contains(rating_filter, case=False, na=False)
        ]

    # Optional summary text
    total = len(agencies_filtered)
    st.markdown(
        f"**Showing {total} agencies** "
        f"({rating_filter if rating_filter != 'All' else 'All ratings'})"
    )


    marker_cluster = MarkerCluster(name="Homecare Agencies").add_to(m)

    for _, row in agencies_filtered.iterrows():
        # Determine color
        rating_value = str(row.get(rating_col, "N/A")).strip().title() if rating_col else "N/A"
        color = rating_colors.get(rating_value, "gray")

        # Popup info
        popup_html = (
            f"{row.get('Provider name', '')}</b><br>"
            # f"<b>{row["Provider name"]}</b><br>"
            f"{row.get('Location_Name', '')}<br>"
            f"{row.get('Location_Postcode', '')}<br>"
            f"<b>Rating:</b> {rating_value}"
        )

        folium.CircleMarker(
            location=[row["Latitude"], row["Longitude"]],
            radius=5,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.8,
            popup=popup_html,
            tooltip=f"{row.get('Location_Name', row['Provider name'])} — {rating_value}"
            # tooltip=f"{row.get('Location_Name', 'Provider name')} — {rating_value}"
        ).add_to(marker_cluster)

    # Add static legend
    legend_html = """
    <div style="position: fixed; bottom: 30px; left: 30px; width: 160px; height: 160px;
        background-color: white; border:2px solid grey; z-index:9999; font-size:14px; padding: 10px;">
    <b>CQC Ratings</b><br>
    <i style="background:darkgreen; color:darkgreen;">--</i> Outstanding<br>
    <i style="background:green; color:green;">--</i> Good<br>
    <i style="background:orange; color:orange;">--</i> Requires improvement<br>
    <i style="background:red; color:red;">--</i> Inadequate<br>
    <i style="background:gray; color:gray;">--</i> Not yet rated
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

folium.LayerControl(collapsed=False).add_to(m)

# Display Map + Table
st_folium(m, width=None, height=750)
st.markdown("### 📊 Data Table")
st.dataframe(df)