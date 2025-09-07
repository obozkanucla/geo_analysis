import pandas as pd

def load_sample_demand():
    """Return sample demand data (can be replaced with real ONS data later)."""
    sample_demand = {
        "region": ["London", "North West", "South East", "Yorkshire"],
        "population": [9000000, 7300000, 8800000, 5500000],
        "target_population": [1200000, 1600000, 1800000, 900000],
        "target_percent": [13.3, 21.9, 20.5, 16.4]
    }
    return pd.DataFrame(sample_demand)