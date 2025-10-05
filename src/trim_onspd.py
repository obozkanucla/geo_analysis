import pandas as pd
import os
from config import BASE_DIR  # reuse your config path

# --- Paths ---
raw_path = f"{BASE_DIR}/ONSPD_Online_latest_Postcode_Centroids_.csv"       # your big file
trimmed_path = f"{BASE_DIR}/ONSPD_Centroids.csv"     # output (small)

# --- Columns to extract ---
usecols = ["PCDS", "LAT", "LONG", "DOTERM"]  # correct casing for your file
chunksize = 250_000

rows = []
for i, chunk in enumerate(pd.read_csv(raw_path, usecols=usecols, dtype=str, chunksize=chunksize)):
    # Keep active postcodes only: doterm is empty or 'NaN'
    chunk = chunk[chunk["DOTERM"].isna() | (chunk["DOTERM"] == "")]
    # Drop rows missing coordinates
    chunk = chunk.dropna(subset=["LAT", "LONG"])
    # Keep only the needed columns
    chunk = chunk[["PCDS", "LAT", "LONG"]]
    rows.append(chunk)
    print(f"✅ Processed chunk {i+1}, total rows so far: {sum(len(c) for c in rows):,}")

# --- Concatenate and save ---
df = pd.concat(rows, ignore_index=True)
df.to_csv(trimmed_path, index=False)
print(f"\n🎉 Saved trimmed file: {trimmed_path} ({len(df):,} active postcodes)")