# src/geo_utils.py
import geopandas as gpd
import pandas as pd

def load_shapefile(path: str) -> gpd.GeoDataFrame:
    """
    Load a shapefile into a GeoDataFrame.
    Works with Fiona 1.10+ and GeoPandas 0.13.2+.
    """
    return gpd.read_file(path)


def merge_geo_data(geodf: gpd.GeoDataFrame, df: pd.DataFrame, geodf_key: str, df_key: str) -> gpd.GeoDataFrame:
    """
    Merge a GeoDataFrame with a DataFrame on specified columns.
    """
    return geodf.merge(df, left_on=geodf_key, right_on=df_key, how="left")


def prepare_map_data(map_df: gpd.GeoDataFrame, value_column: str) -> gpd.GeoDataFrame:
    """
    Fill missing values for choropleth mapping.
    """
    map_df[value_column] = map_df[value_column].fillna(0)
    return map_df