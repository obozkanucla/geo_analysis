import json

geojson_path = "/Users/obozkan/Library/Mobile Documents/com~apple~CloudDocs/__Python/geo_analysis/data/Major_Towns_and_Cities_Dec_2015_Boundaries_V2_2022_121402779136482658.geojson"

with open(geojson_path) as f:
    geo = json.load(f)

print(geo["features"][0]["properties"].keys())