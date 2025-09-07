import pandas as pd

def load_population(csv_path):
    """Load population CSV and return cleaned DataFrame."""
    df = pd.read_csv(csv_path, skiprows=3)  # skip header rows if needed
    df['LAD25NM'] = df['Area'].apply(lambda x: x.split(':')[-1].split()[0])
    return df

def aggregate_by_LAD(df):
    """Aggregate population per LAD."""
    pop_cols = [c for c in df.columns if 'Aged' in c or c=='Total']
    agg_df = df.groupby('LAD25NM')[pop_cols].sum().reset_index()
    return agg_df