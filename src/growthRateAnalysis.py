import os

import pandas as pd
import sys
from pathlib import Path
from rapidfuzz import process, fuzz

sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))
from config import (CITIES_GEOJSON, LAD_GEOJSON, REGION_GEOJSON, COUNTY_GEOJSON, LAD_POP_CSV, LAD_POP_CSV_AGG,
                    LAD_TO_REGION_MAPPING, LAD_TO_COUNTY_MAPPING, COMPANIES_HOUSE_DATA, HOMECARE_AGENCIES)

# ---------- 2. Clean Company Names ----------
def clean_name(name):
    if pd.isna(name):
        return ""
    name = name.lower().strip()
    name = name.replace("limited", "ltd")  # normalize
    name = ''.join(c for c in name if c.isalnum() or c.isspace())
    return " ".join(name.split())

def fuzzy_match(name, cutoff=85):
    match = process.extractOne(name, choices, scorer=fuzz.token_sort_ratio, score_cutoff=cutoff)
    return match[0] if match else None, match[1] if match else None

# ---------- 5. Combine Exact + Fuzzy ----------
def pick_company(row):
    if pd.notna(row["CompanyName"]):
        return row["CompanyName"], row.get("IncorporationDate")
    elif pd.notna(row.get("CompanyName_ch_fuzzy")):
        return row["CompanyName_ch_fuzzy"], row.get("IncorporationDate_ch_fuzzy")
    else:
        return None, None

def do_the_matching():
    # ---------- 1. Load Data ----------
    cqc = pd.read_csv(HOMECARE_AGENCIES)
    ch = pd.read_csv(COMPANIES_HOUSE_DATA)
    cqc["clean_name"] = cqc["Provider name"].astype(str).apply(clean_name)
    ch["clean_name"] = ch["CompanyName"].astype(str).apply(clean_name)

    # ---------- 3. Exact Merge ----------
    merged = cqc.merge(ch, on="clean_name", how="left", suffixes=("_cqc", "_ch"))

    # ---------- 4. Fuzzy Match Only Unmatched ----------
    unmatched = merged[merged["CompanyName"].isna()].copy()
    choices = ch["clean_name"].tolist()
    unmatched["fuzzy_match"], unmatched["match_score"] = zip(*unmatched["clean_name"].apply(fuzzy_match))

    # Merge fuzzy matches back to Companies House data
    unmatched = unmatched.merge(
        ch, left_on="fuzzy_match", right_on="clean_name", how="left", suffixes=("", "_ch_fuzzy")
    )

    merged[["final_company_name", "incorporation_date"]] = merged.apply(pick_company, axis=1, result_type="expand")
    merged["incorporation_date"] = pd.to_datetime(merged["incorporation_date"], errors="coerce")

    # ---------- 6. Calculate Company Age ----------
    merged["company_age_years"] = (pd.Timestamp.today() - merged["incorporation_date"]).dt.days / 365.25

    # ---------- 7. Report ----------
    total = len(merged)
    matched = merged["final_company_name"].notna().sum()
    unmatched_count = total - matched

    print(f"Total CQC providers: {total}")
    print(f"Matched with Companies House (exact or fuzzy): {matched} ({matched/total:.1%})")
    print(f"Unmatched: {unmatched_count} ({unmatched_count/total:.1%})")

    # ---------- 8. Export ----------
    merged.to_csv("cqc_companies_merged.csv", index=False)
    print("Merged dataset saved to cqc_companies_merged.csv")

def do_the_leftover_matching():
    trading_candidates_filename = "trading_candidates.csv"
    if not os.path.exists(trading_candidates_filename):

        merged_cqc = pd.read_csv("cqc_companies_merged.csv")
        print(merged_cqc.columns)

        leftovers = merged_cqc[merged_cqc[" CompanyNumber"].isna()].copy()

        # Prepare companies house data for matching

        # Keywords to exclude
        exclude_keywords = [
            "Limited", "Ltd", "LTD", "LLP", "PLC", "Council", "NHS", "Hospital",
            "Mrs", "Borough", "Miss", "Mr", "Ms", "Service", "Foundation",
            "Society", "Association", "Trust", "CIO", "Charitable", "Community Interest",
            "School"
        ]
        # Filter function
        def is_trading_name(name):
            if pd.isna(name):
                return False
            return not any(keyword.lower() in name.lower() for keyword in exclude_keywords)

        # Apply filter
        trading_candidates = leftovers[leftovers["Provider name"].apply(is_trading_name)]
        # Save filtered list
        trading_candidates.to_csv("trading_candidates.csv", index=False)
    else:
        trading_candidates = pd.read_csv(trading_candidates_filename)
    ch = pd.read_csv(COMPANIES_HOUSE_DATA)
    ch["clean_name"] = ch["CompanyName"].astype(str).apply(clean_name)

    print(f"Filtered {len(trading_candidates)} potential trading names for 'Ltd' matching.")

    # ---------- 1. Create variants ----------
    def generate_ltd_variants(name):
        clean = name.strip()
        return [clean, f"{clean} ltd", f"{clean} limited"]

    # Expand leftovers with variants
    leftovers_expanded = trading_candidates.copy()
    leftovers_expanded["variants"] = leftovers_expanded["Provider name"].apply(generate_ltd_variants)

    # Explode variants into separate rows
    leftovers_exploded = leftovers_expanded.explode("variants").rename(columns={"variants": "variant_name"})

    # Clean variant names for matching
    leftovers_exploded["clean_variant"] = leftovers_exploded["variant_name"].apply(clean_name)

    # ---------- 2. Merge with Companies House ----------
    merged_ltd = leftovers_exploded.merge(
        ch, left_on="clean_variant", right_on="clean_name", how="left", suffixes=("_cqc", "_ch")
    )
    # after merging variants
    if "match_score" not in merged_ltd.columns:
        merged_ltd["match_score"] = 100  # assume perfect match for added Ltd variants

    merged_ltd = merged_ltd.sort_values("match_score", ascending=False)  # pick best match first
    merged_ltd = merged_ltd.drop_duplicates(subset="Provider name", keep="first")
    # print(merged_ltd.columns.tolist())
    # ---------- 3. Stats ----------
    total_leftovers = len(leftovers_exploded["Provider name"].unique())
    # Providers that got at least one match
    matched_providers = merged_ltd.loc[merged_ltd[" CompanyNumber_ch"].notna(), "Provider name"].unique()
    matched_after_ltd = len(matched_providers)

    # Remaining unmatched
    remaining_unmatched = total_leftovers - matched_after_ltd

    print(f"Total leftover providers: {total_leftovers}")
    print(f"Matched after adding Ltd/Limited: {matched_after_ltd} ({matched_after_ltd / total_leftovers:.1%})")
    print(f"Still unmatched: {remaining_unmatched} ({remaining_unmatched / total_leftovers:.1%})")

    # ---------- 4. Check new matches ----------
    new_matches = merged_ltd[merged_ltd[" CompanyNumber_ch"].notna()]
    unmatched = merged_ltd[merged_ltd[" CompanyNumber_ch"].isna()]

    print(f"New matches after adding Ltd/Limited: {len(new_matches)}")
    print(f"Still unmatched after adding Ltd/Limited: {len(unmatched)}")

    # ---------- 5. Save results ----------
    merged_ltd.to_csv("leftovers_ltd_merged.csv", index=False)
    new_matches.to_csv("matched_after_ltd.csv", index=False)
    unmatched.to_csv("still_unmatched_after_ltd.csv", index=False)

    print("Saved Ltd/Limited merge results to leftovers_ltd_merged.csv")
    print("Saved matched providers to matched_after_ltd.csv")
    print("Saved unmatched providers to still_unmatched_after_ltd.csv")

if __name__ == "__main__":
    # do_the_matching()
    do_the_leftover_matching()
