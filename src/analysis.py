import pandas as pd

def merge_demand_supply(demand_df: pd.DataFrame, supply_df: pd.DataFrame):
    """Merge demand and supply dataframes on 'region'"""
    return demand_df.merge(supply_df, on="region", how="left")

def compute_saturation(df: pd.DataFrame):
    """Compute companies per 1k target population"""
    df["companies_per_1k"] = df["num_companies"] / (df["target_population"] / 1000)
    return df