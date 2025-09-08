import pandas as pd
import sys
from pathlib import Path

# =============================
# Paths & imports
# =============================
sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))
from config import POSTCODE_MAPPING, HOMECARE_AGENCIES

# =============================
# Load datasets
# =============================
cqc = pd.read_csv(HOMECARE_AGENCIES)
postcode_map = pd.read_csv(POSTCODE_MAPPING)

# Normalize postcodes
cqc["Postcode"] = cqc["Postcode"].str.upper().str.strip()
postcode_map["pcds"] = postcode_map["pcds"].str.upper().str.strip()

# Optional: check duplicates before merge
dup_counts = cqc.duplicated(subset=["Name"], keep=False).sum()
print("Duplicate agencies before merge:", dup_counts)

# =============================
# Merge on postcode to get LADs
# =============================
cqc_geo = cqc.merge(
    postcode_map[["pcds","oa21cd","lsoa21cd","lsoa21nm",
                  "msoa21cd","msoa21nm","ladcd","ladnm"]],
    left_on="Postcode", right_on="pcds", how="left"
)

dup_counts = cqc_geo.duplicated(subset=["Name"], keep=False).sum()
print("Duplicate agencies due to merge:", dup_counts)

# =============================
# Aggregate number of agencies per LAD
# =============================
agg_lad = cqc_geo.groupby("ladnm")["Name"].count().reset_index(name="Total_Agencies")

# =============================
# Aggregate number of agencies per LAD per CQC rating
# =============================
agg_lad_cqc = cqc_geo.pivot_table(
    index="ladnm",
    columns="CQC_Rating",
    values="Name",
    aggfunc="count",
    fill_value=0
).reset_index()

# Optional: compute percentages per rating
rating_cols = [col for col in agg_lad_cqc.columns if col != "ladnm"]
for col in rating_cols:
    agg_lad_cqc[f"{col}_pct"] = (agg_lad_cqc[col] / agg_lad_cqc[rating_cols].sum(axis=1)) * 100

# Merge total agencies for completeness
agg_lad_cqc = agg_lad_cqc.merge(agg_lad, on="ladnm", how="left")

# =============================
# Save outputs
# =============================
raw_path = Path(HOMECARE_AGENCIES)
data_folder = raw_path.parent.parent / 'data'  # assuming raw_path is in "src"

CQCDataPostCodeFileName = data_folder / f"{raw_path.stem}_postcodes{raw_path.suffix}"
CQCDataLADFileName = data_folder / f"{raw_path.stem}_LAD{raw_path.suffix}"
CQCDataLADCQCFileName = data_folder / f"{raw_path.stem}_LAD_CQC_counts{raw_path.suffix}"

# Save
cqc_geo.to_csv(CQCDataPostCodeFileName, index=False)
agg_lad.to_csv(CQCDataLADFileName, index=False)
agg_lad_cqc.to_csv(CQCDataLADCQCFileName, index=False)

print("Saved postcode-level, LAD-level, and LAD-CQC-level aggregates.")