# app/main.py
import sys
from pathlib import Path
import streamlit as st
import matplotlib.pyplot as plt

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Import our modules
from src.demand_loader import load_sample_demand
from src.supply_loader import load_sample_supply
from src.analysis import merge_demand_supply, compute_saturation
from src.geo_utils import load_shapefile, merge_geo_data, plot_choropleth

# gdf = load_shapefile("data/LAD_MAY_2025_UK_BGC_V2_2682909471764968542/LAD_MAY_2025_UK_BGC_V2.shp")
gdf = load_shapefile("/Users/obozkan/Library/Mobile Documents/com~apple~CloudDocs/"
                     "__Python/geo_analysis/data/LAD_MAY_2025_UK_BGC_V2_2682909471764968542/LAD_MAY_2025_UK_BGC_V2.shp")
print(gdf.columns)
print(gdf.head())