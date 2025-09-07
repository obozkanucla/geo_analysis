import pandas as pd
import sys
from pathlib import Path
from config import CITIES_GEOJSON, LAD_GEOJSON, REGION_GEOJSON, COUNTY_GEOJSON, LAD_POP_CSV, MASTER_MAPPING, WARD_TO_LAD_MAPPING

sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))
from config import CITIES_GEOJSON, LAD_GEOJSON, REGION_GEOJSON, COUNTY_GEOJSON, LAD_POP_CSV, MASTER_MAPPING

# 1️⃣ Load your data
pop_data = pd.read_csv(LAD_POP_CSV, skiprows=5)  # adjust skiprows as required

# 2️⃣ Split first column into three fields
pop_data[['GeoType', 'LSOA21_Code', 'LSOA_Name']] = pop_data.iloc[:,0].str.split(r'[:]', expand=True)
pop_data['LSOA21_Code'] = pop_data['LSOA21_Code'].str.strip()
pop_data['LSOA_Name'] = pop_data['LSOA_Name'].str.replace(':','').str.strip()

# 3️⃣ Load ONS LSOA-to-Ward-LAD lookup
lookup = pd.read_csv(WARD_TO_LAD_MAPPING)

# 4️⃣ Merge on LSOA code
merged = pop_data.merge(lookup, left_on='LSOA21_Code', right_on='LSOA21CD', how='left')

# Create a mask for rows where the first column starts with "lsoa"
lsoa_rows = pop_data['GeoType'].str.lower().str.startswith('lsoa')

# 5️⃣ Check for unmatched entries
unmatched = merged[lsoa_rows & merged['WD23NM'].isna()]

if len(unmatched) > 0:
    print("Unmatched LSOAs found:")
    print(unmatched[['LSOA21_Code','LSOA_Name']])
else:
    print("All LSOAs matched. Ready to aggregate.")

# 6️⃣ Aggregate to LAD
# Example for a column named 'Population'
# Aggregate by LAD
# Columns to aggregate
pop_cols = [c for c in merged.columns if 'Aged' in c or c == 'Total']
raw_path = Path(LAD_POP_CSV)

# Define the "data" folder at the same level as "src"
data_folder = raw_path.parent.parent / 'data'  # assuming raw_path is in "src"
data_folder.mkdir(exist_ok=True)  # create if it doesn't exist

# Output merged CSV in data folder
output_path_merged = data_folder / f"{raw_path.stem}_merged{raw_path.suffix}"
merged.to_csv(output_path_merged, index=False)

# Aggregate to LAD
agg_df = merged.groupby('LAD23NM')[pop_cols].sum().reset_index()

# Output aggregated CSV in data folder
output_path_aggregated = data_folder / f"{raw_path.stem}_aggregated{raw_path.suffix}"
agg_df.to_csv(output_path_aggregated, index=False)