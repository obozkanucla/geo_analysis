import pandas as pd
from pathlib import Path

# Config
DATA_DIR = Path("/Users/obozkan/PycharmProjects/geo_analysis/data")

AGENCIES = DATA_DIR / "HomeCareAgencies_data (08-09-2025)(ALL_CQC_RATINGS)_postcodes.csv"
ONSPD = DATA_DIR / "ONSPD_Centroids.csv"     # your large file
OUTPUT = DATA_DIR / "postcode_centroids_small.csv"

print("📥 Loading agency postcodes...")
df = pd.read_csv(AGENCIES)
df["pcds_clean"] = df["pcds"].str.replace(" ", "").str.upper()

print("📥 Loading ONSPD centroids (FULL)… this may take a moment…")
cent = pd.read_csv(ONSPD, usecols=["PCDS", "LAT", "LONG"])
cent["pcds_clean"] = cent["PCDS"].str.replace(" ", "").str.upper()

print("🔍 Selecting only required postcodes…")
needed = cent[cent["pcds_clean"].isin(df["pcds_clean"].unique())]

print(f"💾 Saving trimmed centroid file → {OUTPUT}")
needed.to_csv(OUTPUT, index=False)

print("✅ Done! Reduced from 415MB → a few MB.")
print(f"Final rows: {len(needed):,}")