# config.py

# =============================
# Data paths
# =============================
# config.py
import os

# Base directory relative to this config.py file
BASE_DIR = os.path.join(os.path.dirname(__file__), "../data")

# BASE_DIR = "/Users/obozkan/Library/Mobile Documents/com~apple~CloudDocs/__Python/geo_analysis/data"

CITIES_GEOJSON = f"{BASE_DIR}/Major_Towns_and_Cities_Dec_2015_Boundaries_V2_2022_121402779136482658.geojson"
LAD_GEOJSON = f"{BASE_DIR}/LAD_MAY_2025_UK_BGC_V2_1110015208521213948.geojson"
#REGION_GEOJSON = f"{BASE_DIR}/Regions_December_2024_Boundaries_EN_BUC_4744747487989771477.geojson"
REGION_GEOJSON = f"{BASE_DIR}/European_Electoral_Regions_Dec_2017_UK_BSC_2022_2476479127562833087.geojson"
# COUNTY_GEOJSON = f"{BASE_DIR}/Counties_December_2024_Boundaries_EN_BFC_-3795571296904775948.geojson"
COUNTY_GEOJSON = f"{BASE_DIR}/Counties_and_Unitary_Authorities_December_2023_Boundaries_UK_BSC_4952317392296043005.geojson"
LAD_POP_CSV = f"{BASE_DIR}/PopulationStatsByLADDetail.csv"
LAD_POP_CSV_AGG = f"{BASE_DIR}/PopulationStatsByLADDetail_aggregated.csv"
LAD_TO_REGION_MAPPING = f"{BASE_DIR}/Local_Authority_District_to_Region_(December_2023)_Lookup_in_England.csv"
LAD_TO_COUNTY_MAPPING = f"{BASE_DIR}/Local_Authority_District_to_County_and_Unitary_Authority_(April_2023)_Lookup_in_EW.csv"
MASTER_MAPPING = f"{BASE_DIR}/Ward_to_Local_Authority_District_to_County_to_Region_to_Country_(May_2023)_Lookup_in_United_Kingdom.csv"
WARD_TO_LAD_MAPPING = f"{BASE_DIR}/LSOA_(2021)_to_Electoral_Ward_(2023)_to_LAD_(2023)_Best_Fit_Lookup_in_EW.csv"
POSTCODE_MAPPING = f"{BASE_DIR}/PCD_OA21_LSOA21_MSOA21_LAD_MAY25_UK_LU.csv"
# HOMECARE_AGENCIES = f"{BASE_DIR}/HomeCareAgencies_data (08-09-2025)(ALL_RATINGS).csv"
HOMECARE_AGENCIES = f"{BASE_DIR}/HomeCareAgencies_data (08-09-2025)(ALL_CQC_RATINGS).csv"
HOMECARE_AGENCIES_BY_LAD = f"{BASE_DIR}/HomeCareAgencies_data (08-09-2025)(ALL_CQC_RATINGS)_LAD_CQC_counts.csv"
# =============================
# Map settings
# =============================
MAP_CENTER = [54.5, -3]
ZOOM_START = 5