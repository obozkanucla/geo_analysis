import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

from config import BASE_DIR, HOMECARE_AGENCIES
from config import LAD_TO_COUNTY_MAPPING
import os
import json

# Load agencies
agencies_df = pd.read_csv(HOMECARE_AGENCIES)
agencies_df["Postcode"] = agencies_df["Postcode"].str.strip().str.upper()

# Load centroids
onspd_path = f"{BASE_DIR}/ONSPD_Centroids.csv"
if os.path.exists(onspd_path):
    centroids = pd.read_csv(onspd_path, usecols=["PCDS", "LAT", "LONG"])
    centroids["PCDS"] = centroids["PCDS"].str.strip().str.upper()
    agencies_df = agencies_df.merge(centroids, left_on="Postcode", right_on="PCDS", how="left")
    agencies_df.rename(columns={"LAT": "Latitude", "LONG": "Longitude"}, inplace=True)
    agencies_df = agencies_df.dropna(subset=["Latitude", "Longitude"])
else:
    st.error("❌ ONSPD_Centroids.csv missing. Cannot map agencies.")
    st.stop()

# Load LAD → County mapping
lad_map = pd.read_csv(LAD_TO_COUNTY_MAPPING)
lad_dict = dict(zip(lad_map["LTLA23NM"], lad_map["UTLA23NM"]))

# Attach county
if "ladnm" in agencies_df.columns:
    agencies_df["County"] = agencies_df["ladnm"].map(lad_dict)
elif "LAD23NM" in agencies_df.columns:
    agencies_df["County"] = agencies_df["LAD23NM"].map(lad_dict)
else:
    agencies_df["County"] = None

# User-selected counties
target_counties = [
    "Lincolnshire",
    "Suffolk",
    "Cambridgeshire",
    "Essex",
    "Leicestershire",
]

agencies_5 = agencies_df[agencies_df["County"].isin(target_counties)]

st.title("🏥 Homecare Agencies in 5 Counties")

st.write(f"Found **{len(agencies_5)}** agencies in the selected counties.")
st.dataframe(agencies_5)

# Map
m = folium.Map(location=[52.9, -0.5], zoom_start=7)

for _, row in agencies_5.iterrows():
    folium.CircleMarker(
        location=[row["Latitude"], row["Longitude"]],
        radius=4,
        color="blue",
        fill=True,
        fill_opacity=0.7,
        popup=row.get("Provider name", ""),
        tooltip=row.get("Provider name", "")
    ).add_to(m)

st_folium(m, height=700)