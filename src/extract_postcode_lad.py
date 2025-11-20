# extract_postcode_lad.py
import pandas as pd
from pathlib import Path

INPUT = Path("/Users/obozkan/PycharmProjects/geo_analysis/data/PCD_OA21_LSOA21_MSOA21_LAD_MAY25_UK_LU.csv")
OUTPUT = Path("/Users/obozkan/PycharmProjects/geo_analysis/data/postcode_to_lad.csv")

CHUNKSIZE = 200_000

print("Extracting PCD → LAD mapping…")

reader = pd.read_csv(INPUT, chunksize=CHUNKSIZE)

chunks = []

for chunk in reader:
    chunk.columns = chunk.columns.str.lower()

    # Make sure columns exist
    if "pcds" not in chunk or "ladnm" not in chunk:
        raise ValueError("Required columns ('pcds', 'ladnm') not found in chunk.")

    # Select needed columns
    sub = chunk[["pcds", "ladnm"]].dropna()

    # Clean full postcode (remove space)
    sub["pcds_clean"] = (
        sub["pcds"]
        .astype(str)
        .str.upper()
        .str.replace(" ", "")
        .str.strip()
    )

    chunks.append(sub[["pcds_clean", "ladnm"]])

# Combine and remove duplicates
lookup = pd.concat(chunks).drop_duplicates()

print(f"Saving lookup with {len(lookup):,} rows → {OUTPUT}")
lookup.to_csv(OUTPUT, index=False)

print("Done ✔")