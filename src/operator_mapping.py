"""
CQC Market Structure Analysis Helpers
-------------------------------------
Original and restored market entity grouping logic.
"""

import re
import pandas as pd


# ---------------------------------------------------------
# Group and Franchise Definitions
# ---------------------------------------------------------

group_mapping = {
    "Cera Care": [
        "Cera Care", "Cera Homecare", "Cera Care Carers", "Cera Care Central",
        "Cera Care Germany", "Cera Care Operations", "Cera Care Technology",
        "Apex Prime Care", "Apex Prime Care Holdings", "Apex Prime Care Group",
        "Mediline Home Care", "Nobilis Care", "Premier Care", "Velvet Glove Care",
        "Cardiff Homecare", "Homecare4U", "Alpenbest", "Care Quality Services",
        "Allied Health Support", "Gemcare South West", "BruDi Homecare"
    ],
    "Helping Hands": ["Midshires Care Limited", "Helping Hands"],
    "McCarthy & Stone": ["Yourlife Management Services Limited", "McCarthy & Stone"],
    "Radis Group": ["G P Homecare Limited", "Radis Community Care"],
    "Housing 21": ["Housing 21"],
    "Creative Support": ["Creative Support Limited", "Creative Support"],
    "Achieve Together": ["Achieve Together Limited", "Achieve Together"],
    "Mencap": ["Royal Mencap Society", "Mencap"],
    "Voyage Care": ["Voyage 1 Limited", "Voyage Care"],
    "Care Outlook": ["Care Outlook Ltd", "Care Outlook"],
}

franchise_mapping = {
    "Home Instead": "Home Instead",
    "Bluebird Care": "Bluebird Care",
    "Caremark": "Caremark",
    "Right at Home": "Right at Home",
    "Kare Plus": "Kare Plus",
    "Radfield": "Radfield Home Care",
    "Walfinch": "Walfinch",
    "PerCurra": "PerCurra",
    "Hallows": "Hallows Care",
    "Good Oaks": "Good Oaks Home Care",
    "Prestige": "Prestige Nursing & Care",
    "Everycare": "Everycare",
    "ComForcare": "ComForcare",
    "Extra Help": "Extra Help",
    "Avant Healthcare": "Avant Healthcare",
    "Seniors Helping Seniors": "Seniors Helping Seniors",
    "Apollo Care": "Apollo Care",
    "Heritage": "Heritage Healthcare",
    "Sylvian": "SylvianCare",
    "Blossom": "Blossom Home Care",
    "Nurse Next Door": "Nurse Next Door",
    "Homewatch": "Homewatch CareGivers",
    "Interim HealthCare": "Interim HealthCare",
    "Lastminute Care": "Lastminute Care & Nursing",
}

true_franchises = list(franchise_mapping.values())


# ---------------------------------------------------------
# Cleaning helper
# ---------------------------------------------------------

def clean_name(name: str) -> str:
    if not isinstance(name, str):
        return ""
    name = re.sub(r"[–—−]", "-", name)
    name = " ".join(name.split())
    name = re.sub(r"[^\w\s-]", "", name)
    return name.lower().strip()


# ---------------------------------------------------------
# Mapping Functions — RESTORED ORIGINAL LOGIC
# ---------------------------------------------------------

def map_franchise_row(row):
    """Apply franchise detection first on Name, then Provider name."""
    name_clean = clean_name(row.get("Name", ""))
    provider_clean = clean_name(row.get("Provider name", ""))

    # Special case for Home Instead
    if "home instead" in name_clean or "home instead" in provider_clean:
        return "Home Instead"

    # Try location name first (old behaviour)
    for keyword, brand in franchise_mapping.items():
        if clean_name(keyword) in name_clean:
            return brand

    # Fall back to provider legal name
    for keyword, brand in franchise_mapping.items():
        if clean_name(keyword) in provider_clean:
            return brand

    return None


def map_corporate_group(provider_name: str):
    name = str(provider_name).lower()
    for parent, subs in group_mapping.items():
        for s in subs:
            if s.lower() in name:
                return parent
    return None


def classify_operator(row):
    if row.get("Franchise") in true_franchises:
        return "Franchise group"
    if row.get("num_agencies", 0) > 1:
        return "Multi-location operator (non-franchise)"
    return "Independent small"