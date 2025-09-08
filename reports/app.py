import streamlit as st
import sys
from pathlib import Path

# Make sure src is on the path
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from analysis import aggregate_population_by_level  # example