import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))
from config import (CITIES_GEOJSON, LAD_GEOJSON, REGION_GEOJSON, COUNTY_GEOJSON,
                    LAD_POP_CSV, LAD_POP_CSV_AGG, LAD_TO_REGION_MAPPING, LAD_TO_COUNTY_MAPPING)
from analysis import load_lad_population

lad_region_map = pd.read_csv(LAD_TO_REGION_MAPPING)
print(lad_region_map.columns)

