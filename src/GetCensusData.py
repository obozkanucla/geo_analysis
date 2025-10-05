import pandas as pd
from config import (UK_CENSUS_DATA)
# Read the Table_of_contents sheet to get the sheet names
toc_df = pd.read_excel(UK_CENSUS_DATA, sheet_name="Table_of_contents", skiprows=2)

# Map Table X -> sheet number and descriptive name
sheet_map = {}
for _, row in toc_df.iterrows():
    table_label = row['Table']          # e.g., "Table 1"
    table_number = table_label.split()[1]  # "1"
    sheet_map[table_number] = row['Name']  # descriptive name

# Initialize the combined DataFrame
combined_df = pd.DataFrame()

# Loop through each sheet
for sheet_number, metric_name in sheet_map.items():
    # Read sheet without headers first
    df_raw = pd.read_excel(UK_CENSUS_DATA, sheet_name=sheet_number, header=None)

    # Find header row dynamically
    header_row_index = \
    df_raw[df_raw.apply(lambda row: row.astype(str).str.contains('Area code', case=False).any(), axis=1)].index[0]

    # Read sheet again using correct header row
    df = pd.read_excel(UK_CENSUS_DATA, sheet_name=sheet_number, header=header_row_index)

    # Clean column names and string columns
    df.columns = df.columns.str.strip()
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].str.strip()

    # Drop rows without Area code
    df = df.dropna(subset=['Area code'])

    # Convert Period to numeric
    df['Period'] = pd.to_numeric(df['Period'], errors='coerce')

    # Get latest row per Area code
    latest_df = df.sort_values('Period').groupby('Area code', as_index=False).last()

    # Keep Area name
    latest_df['Area name'] = latest_df['Area name'].str.strip()

    # Identify the value column
    value_col = [col for col in latest_df.columns if col not in ['Area code', 'Area name', 'Period']][0]

    # Keep only Area code, Area name, and the value column renamed to metric
    latest_df = latest_df[['Area code', 'Area name', value_col]].rename(columns={value_col: metric_name})

    # Merge with combined_df
    if combined_df.empty:
        combined_df = latest_df
    else:
        # Merge on Area code and Area name
        combined_df = pd.merge(combined_df, latest_df, on=['Area code', 'Area name'], how='outer')

# Optional: save to CSV
combined_df.to_csv("latest_area_data.csv", index=False)

print("Done! Latest data for each area extracted from all sheets.")