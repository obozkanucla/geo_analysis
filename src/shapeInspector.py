import json

geojson_path = "/Users/obozkan/Library/Mobile Documents/com~apple~CloudDocs/__Python/geo_analysis/data/Regions_December_2024_Boundaries_EN_BUC_4744747487989771477.geojson"

with open(geojson_path) as f:
    geo = json.load(f)

print(geo["features"][0]["properties"].keys())