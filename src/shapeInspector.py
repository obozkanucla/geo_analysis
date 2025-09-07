import json

# geojson_path = "/Users/obozkan/Library/Mobile Documents/com~apple~CloudDocs/__Python/geo_analysis/data/Major_Towns_and_Cities_Dec_2015_Boundaries_V2_2022_121402779136482658.geojson"
geojson_path = "/Users/obozkan/Library/Mobile Documents/com~apple~CloudDocs/__Python/geo_analysis/data/Counties_December_2024_Boundaries_EN_BFC_-3795571296904775948.geojson"
with open(geojson_path) as f:
    geo = json.load(f)

print(geo["features"][0]["properties"].keys())

city_names = [f["properties"]["TCITY15NM"] for f in geo["features"]]
print(city_names)  # print first 20 names