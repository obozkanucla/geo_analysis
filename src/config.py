# config.py

# =============================
# Data paths
# =============================
# config.py
BASE_DIR = "/Users/obozkan/Library/Mobile Documents/com~apple~CloudDocs/__Python/geo_analysis/data"

CITIES_GEOJSON = f"{BASE_DIR}/Major_Towns_and_Cities_Dec_2015_Boundaries_V2_2022_121402779136482658.geojson"
LAD_GEOJSON = f"{BASE_DIR}/LAD_MAY_2025_UK_BGC_V2_1110015208521213948.geojson"
REGION_GEOJSON = f"{BASE_DIR}/Regions_December_2024_Boundaries_EN_BUC_4744747487989771477.geojson"
COUNTY_GEOJSON = f"{BASE_DIR}/Counties_December_2024_Boundaries_EN_BFC_-3795571296904775948.geojson"
LAD_POP_CSV = f"{BASE_DIR}/PopulationStatsByLADDetail.csv"
LAD_POP_CSV_AGG = f"{BASE_DIR}/PopulationStatsByLADDetail_aggregated.csv"
LAD_TO_REGION_MAPPING = f"{BASE_DIR}/Local_Authority_District_to_Region_(December_2023)_Lookup_in_England.csv"
LAD_TO_COUNTY_MAPPING = f"{BASE_DIR}/Local_Authority_District_to_County_and_Unitary_Authority_(April_2023)_Lookup_in_EW.csv"
# =============================
# Map settings
# =============================
MAP_CENTER = [54.5, -3]
ZOOM_START = 5