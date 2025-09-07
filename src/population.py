import pandas as pd

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))
from config import CITIES_GEOJSON, LAD_GEOJSON, REGION_GEOJSON, COUNTY_GEOJSON, LAD_POP_CSV


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

    return str(output_path)
def load_population(csv_path):
    """Load population CSV and return cleaned DataFrame."""
    df = pd.read_csv(LAD_POP_CSV, skiprows=5)  # skip header rows if needed
    df['LAD25NM'] = df['Area'].apply(lambda x: x.split(':')[-1].split()[0])
    return df

def aggregate_by_LAD(df):
    """Aggregate population per LAD."""
    pop_cols = [c for c in df.columns if 'Aged' in c or c=='Total']
    agg_df = df.groupby('LAD25NM')[pop_cols].sum().reset_index()
    return agg_df

# Usage
aggregated_csv = aggregate_lad_population(LAD_POP_CSV, output_dir="aggregated")
print("Aggregated LAD CSV saved at:", aggregated_csv)