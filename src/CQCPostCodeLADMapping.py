import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))
from config import (POSTCODE_MAPPING, HOMECARE_AGENCIES)
# Load datasets
cqc = pd.read_csv(HOMECARE_AGENCIES)
postcode_map = pd.read_csv(POSTCODE_MAPPING)

# Normalize postcodes
cqc["Postcode"] = cqc["Postcode"].str.upper().str.strip()
postcode_map["pcds"] = postcode_map["pcds"].str.upper().str.strip()
dup_counts = cqc.duplicated(subset=["Name"], keep=False).sum()
print("Duplicate agencies before to merge:", dup_counts)

# Merge on postcode
cqc_geo = cqc.merge(postcode_map[["pcds","oa21cd","lsoa21cd","lsoa21nm",
                                  "msoa21cd","msoa21nm","ladcd","ladnm"]],
                    left_on="Postcode", right_on="pcds", how="left")
dup_counts = cqc_geo.duplicated(subset=["Name"], keep=False).sum()
print("Duplicate agencies due to merge:", dup_counts)

# Example aggregation: number of agencies per LAD
agg_lad = cqc_geo.groupby("ladnm")["Name"].count().reset_index(name="Agency_Count")

# Save
raw_path = Path(HOMECARE_AGENCIES)
data_folder = raw_path.parent.parent / 'data'  # assuming raw_path is in "src"

CQCDataPostCodeFileName = data_folder / f"{raw_path.stem}_postcodes{raw_path.suffix}"
CQCDataLADFileName = data_folder / f"{raw_path.stem}_LAD{raw_path.suffix}"

cqc_geo.to_csv(CQCDataPostCodeFileName, index=False)
agg_lad.to_csv(CQCDataLADFileName, index=False)