import pandas as pd
import re

def clean_name(name: str):
    if not isinstance(name, str):
        return ""
    name = name.lower()
    name = re.sub(r"[–—−]", "-", name)
    name = re.sub(r"[^a-z0-9&\-\/\s]", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name

df = pd.read_csv("/Users/obozkan/PycharmProjects/geo_analysis/data/HomeCareAgencies_data (08-09-2025)(ALL_CQC_RATINGS).csv")

sample = df[df["Provider name"].str.contains("Home Instead", case=False, na=False)].copy()
sample["clean_name"] = sample["Provider name"].apply(clean_name)

print(sample[["Provider name", "clean_name"]].head(20))