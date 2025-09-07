import pandas as pd

def merge_demand_supply(demand_df: pd.DataFrame, supply_df: pd.DataFrame):
    """Merge demand and supply dataframes on 'region'"""
    return demand_df.merge(supply_df, on="region", how="left")

def compute_saturation(df: pd.DataFrame):
    """Compute companies per 1k target population"""
    df["companies_per_1k"] = df["num_companies"] / (df["target_population"] / 1000)
    return df

def load_lad_population(csv_path: str) -> pd.DataFrame:
    """Load aggregated LAD population and compute metrics."""
    df = pd.read_csv(csv_path)
    # Compute over-80 ratio
    df['over80_ratio'] = (df['Aged 80 to 84 years'] + df['Aged 85 years and over']) / df['Total']
    return df

def get_top_areas_by_over80_ratio(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Return top n LADs by over-80 ratio."""
    return df.sort_values('over80_ratio', ascending=False).head(n)