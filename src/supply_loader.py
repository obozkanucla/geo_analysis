import pandas as pd

def load_sample_supply():
    """Return sample supply data (number of companies)"""
    sample_supply = {
        "region": ["London", "North West", "South East", "Yorkshire"],
        "num_companies": [250, 140, 180, 95]
    }
    return pd.DataFrame(sample_supply)