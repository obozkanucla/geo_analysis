import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))
from config import CITIES_GEOJSON, LAD_GEOJSON, REGION_GEOJSON, COUNTY_GEOJSON, LAD_POP_CSV, MASTER_MAPPING


def load_master_mapping(mapping_csv_path: str) -> pd.DataFrame:
    """
    Load master hierarchical mapping CSV (Ward → LAD → County → Region → Country)
    """
    df = pd.read_csv(mapping_csv_path)
    # Ensure key columns are consistent
    for col in ["WD23NM", "LAD23NM", "CTY23NM", "RGN23NM", "CTRY23NM"]:
        if col not in df.columns:
            raise ValueError(f"Column {col} not found in mapping CSV")
    return df

def aggregate_population_by_level(pop_df: pd.DataFrame,
                                  mapping_df: pd.DataFrame,
                                  level: str = "LAD") -> pd.DataFrame:
    """
    Aggregate population (or any numeric metric) to a chosen level.
    level: one of ["LAD", "County", "Region", "Country"]
    """
    level_col_map = {
        "LAD": "LAD23NM",
        "County": "CTY23NM",
        "Region": "RGN23NM",
        "Country": "CTRY23NM"
    }
    if level not in level_col_map:
        raise ValueError(f"Invalid level: {level}. Choose from {list(level_col_map.keys())}")

    level_col = level_col_map[level]

    # Merge population metrics with mapping
    df = pop_df.merge(mapping_df[["LAD23NM", "CTY23NM", "RGN23NM", "CTRY23NM"]].drop_duplicates(),
                      left_on="LAD25NM", right_on="LAD23NM", how="left")

    # Identify numeric columns to aggregate
    metric_cols = [c for c in pop_df.columns if c != "LAD25NM"]

    # Group by chosen level
    agg_df = df.groupby(level_col)[metric_cols].sum().reset_index()

    return agg_df

def aggregate_lad_population(raw_csv_path: str, output_dir: str = "data") -> str:
    """
    Aggregate LAD-level population from a raw CSV and save it to a new file
    with '_aggregated' suffix. OA rows are ignored.
    """
    # Load raw CSV (skip headers if needed)
    df = pd.read_csv(raw_csv_path, skiprows=5)  # adjust skiprows as required

    # Keep only LSOA rows
    df = df[df['Area'].str.startswith('lsoa2021:')].copy()

    # Extract LAD name from 'Area' column
    df['LAD25NM'] = df['Area'].apply(lambda x: x.split(':')[-1].strip().split()[0])

    # Columns to aggregate
    pop_cols = [c for c in df.columns if 'Aged' in c or c == 'Total']

    # Aggregate by LAD
    agg_df = df.groupby('LAD25NM')[pop_cols].sum().reset_index()

    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Output file with "_aggregated" suffix
    raw_path = Path(raw_csv_path)
    output_path = Path(output_dir) / f"{raw_path.stem}_aggregated{raw_path.suffix}"
    agg_df.to_csv(output_path, index=False)

    return agg_df

def load_population(csv_path):
    """Load population CSV and return cleaned DataFrame."""
    df = pd.read_csv(LAD_POP_CSV, skiprows=5)  # skip header rows if needed
    df['LADU2023'] = df['Area'].apply(lambda x: x.split(':')[-1].split()[0])
    return df

def aggregate_by_LAD(df):
    """Aggregate population per LAD."""
    pop_cols = [c for c in df.columns if 'Aged' in c or c=='Total']
    agg_df = df.groupby('LAD25NM')[pop_cols].sum().reset_index()
    return agg_df

# Usage
mapping_df = load_master_mapping(MASTER_MAPPING)
aggregated_csv = aggregate_lad_population(LAD_POP_CSV, output_dir="aggregated")
lad_agg = aggregate_population_by_level(aggregated_csv, mapping_df, level="LAD")
county_agg = aggregate_population_by_level(aggregated_csv, mapping_df, level="County")
region_agg = aggregate_population_by_level(aggregated_csv, mapping_df, level="Region")

lad_agg.to_csv(LAD_POP_CSV + 'lad_agg', index=False)
county_agg.to_csv(LAD_POP_CSV + 'county_agg', index=False)
region_agg.to_csv(LAD_POP_CSV + 'region_agg', index=False)

print("Aggregated LAD CSV saved at:", lad_agg)