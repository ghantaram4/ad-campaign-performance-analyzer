from pathlib import Path
import sys
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

@pytest.fixture
def raw():
    return pd.read_csv(ROOT / 'data/social_media_advertising_sample.csv')

@pytest.fixture
def data(raw):
    from utils.data_processing import clean_data
    return clean_data(raw)
