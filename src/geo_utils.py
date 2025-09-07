import geopandas as gpd

def load_geojson(path: str) -> gpd.GeoDataFrame:
    return gpd.read_file(path, engine="pyogrio")