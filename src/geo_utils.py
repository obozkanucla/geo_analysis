import geopandas as gpd
import pandas as pd
import sys
from pathlib import Path
from config import CITIES_GEOJSON, LAD_GEOJSON, REGION_GEOJSON, COUNTY_GEOJSON, LAD_POP_CSV, MASTER_MAPPING, WARD_TO_LAD_MAPPING
sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))
from config import CITIES_GEOJSON, LAD_GEOJSON, REGION_GEOJSON, COUNTY_GEOJSON, LAD_POP_CSV, MASTER_MAPPING
# Load the GeoJSON
county_gdf = gpd.read_file(COUNTY_GEOJSON)
print(county_gdf.columns)

# List all county names
geojson_names = county_gdf['CTYUA23NM'].tolist()
print(geojson_names)

# Full list of UTLA/County names
utla_list = [
    "Hartlepool","Middlesbrough","Redcar and Cleveland","Stockton-on-Tees",
    "Darlington","Halton","Warrington","Blackburn with Darwen","Blackpool",
    "Kingston upon Hull, City of","East Riding of Yorkshire","North East Lincolnshire",
    "North Lincolnshire","York","Derby","Leicester","Rutland","Nottingham",
    "Herefordshire, County of","Telford and Wrekin","Stoke-on-Trent",
    "Bath and North East Somerset","Bristol, City of","North Somerset","South Gloucestershire",
    "Plymouth","Torbay","Swindon","Peterborough","Luton","Southend-on-Sea",
    "Thurrock","Medway","Bracknell Forest","West Berkshire","Reading","Slough",
    "Windsor and Maidenhead","Wokingham","Milton Keynes","Brighton and Hove",
    "Portsmouth","Southampton","Isle of Wight","County Durham","Cheshire East",
    "Cheshire West and Chester","Shropshire","Cornwall","Isles of Scilly","Wiltshire",
    "Bedford","Central Bedfordshire","Essex","Gloucestershire","Hampshire","Hertfordshire",
    "Kent","Lancashire","Croydon","Ealing","Enfield","Greenwich","Hackney",
    "Hammersmith and Fulham","Haringey","Harrow","Havering","Hillingdon","Hounslow",
    "Islington","Kensington and Chelsea","Kingston upon Thames","Lambeth","Lewisham",
    "Merton","Newham","Redbridge","Richmond upon Thames","Southwark","Sutton",
    "Tower Hamlets","Waltham Forest","Wandsworth","Westminster","Cambridgeshire",
    "Derbyshire","Devon","East Sussex","Leicestershire","Lincolnshire","Norfolk",
    "Nottinghamshire","Oxfordshire","Staffordshire","Suffolk","Surrey","Warwickshire",
    "West Sussex","Worcestershire","Isle of Anglesey","Gwynedd","Conwy","Denbighshire",
    "Flintshire","Wrexham","Ceredigion","Pembrokeshire","Carmarthenshire","Swansea",
    "Neath Port Talbot","Bridgend","Vale of Glamorgan","Cardiff","Rhondda Cynon Taf",
    "Caerphilly","Blaenau Gwent","Torfaen","Monmouthshire","Newport","Powys",
    "Merthyr Tydfil","Northumberland","Bournemouth, Christchurch and Poole","Dorset",
    "Buckinghamshire","North Northamptonshire","West Northamptonshire","Cumberland",
    "Westmorland and Furness","North Yorkshire","Somerset","Bolton","Bury","Manchester",
    "Oldham","Rochdale","Salford","Stockport","Tameside","Trafford","Wigan","Knowsley",
    "Liverpool","St. Helens","Sefton","Wirral","Barnsley","Doncaster","Rotherham",
    "Sheffield","Newcastle upon Tyne","North Tyneside","South Tyneside","Sunderland",
    "Birmingham","Coventry","Dudley","Sandwell","Solihull","Walsall","Wolverhampton",
    "Bradford","Calderdale","Kirklees","Leeds","Wakefield","Gateshead","City of London",
    "Barking and Dagenham","Barnet","Bexley","Brent","Bromley","Camden"
]

# Check which are missing in the GeoJSON
missing = [name for name in utla_list if name not in geojson_names]

print(f"Total UTLA entries in GeoJSON: {len(geojson_names)}")
print(f"Missing entries: {missing}")

# Optional: check if specific counties exist
check_counties = ["Cumbria", "Powys", "Cardiff"]
for county in check_counties:
    print(f"{county} in map?:", county in counties)


# # Inspect first few rows
# print(lad_gdf.head())
# print(lad_gdf.columns)
# # List all LAD names in the map
# regions = lad_gdf['eer17nm'].tolist()
# # List all region names
# print("Regions in GeoJSON:", regions)
#
# # Check specifically for Wales
# if "Wales" in regions:
#     print("Wales is covered in the region GeoJSON.")
# else:
#     print("Wales is missing from the region GeoJSON.")
# # List all region names
# regions = region_gdf['RGN24NM'].tolist()
# print("Regions in GeoJSON:", regions)
#
# # Check specifically for Wales
# if "Wales" in regions:
#     print("Wales is covered in the region GeoJSON.")
# else:
#     print("Wales is missing from the region GeoJSON.")
# #
# # # Example: Welsh LADs to check
# # welsh_lads = [
# #     "Isle of Anglesey", "Gwynedd", "Conwy", "Denbighshire", "Flintshire",
# #     "Wrexham", "Powys", "Ceredigion", "Pembrokeshire", "Carmarthenshire",
# #     "Swansea", "Neath Port Talbot", "Bridgend", "Vale of Glamorgan",
# #     "Cardiff", "Rhondda Cynon Taf", "Merthyr Tydfil", "Caerphilly",
# #     "Blaenau Gwent", "Torfaen", "Monmouthshire", "Newport"
# # ]
# #
# # # Check which Welsh LADs are missing in the map
# # missing_welsh_lads = [lad for lad in welsh_lads if lad not in map_lads]
# # if missing_welsh_lads:
# #     print("Missing Welsh LADs in GeoJSON:", missing_welsh_lads)
# # else:
# #     print("All Welsh LADs are covered in the GeoJSON.")