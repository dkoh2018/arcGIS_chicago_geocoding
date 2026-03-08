import pandas as pd
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


# data integrity tests

def test_raw_data_exists():
    path = os.path.join(DATA_DIR, "chicago_crimes_raw.csv")
    assert os.path.exists(path), "raw data file missing"

def test_geocoded_data_exists():
    path = os.path.join(DATA_DIR, "geocoded_results.csv")
    assert os.path.exists(path), "geocoded results file missing"

def test_raw_data_has_expected_columns():
    df = pd.read_csv(os.path.join(DATA_DIR, "chicago_crimes_raw.csv"))
    expected = ["block", "latitude", "longitude"]
    for col in expected:
        assert col in df.columns, f"missing column: {col}"

def test_geocoded_data_has_expected_columns():
    df = pd.read_csv(os.path.join(DATA_DIR, "geocoded_results.csv"))
    expected = ["block", "gc_address", "gc_score", "gc_lat", "gc_lng", "distance_m"]
    for col in expected:
        assert col in df.columns, f"missing column: {col}"

def test_no_empty_blocks():
    df = pd.read_csv(os.path.join(DATA_DIR, "geocoded_results.csv"))
    assert df["block"].notna().all(), "some block addresses are null"


# --- geocoding quality tests ---

def test_match_rate_above_90_percent():
    df = pd.read_csv(os.path.join(DATA_DIR, "geocoded_results.csv"))
    matched = df["gc_score"].notna().sum()
    rate = matched / len(df)
    assert rate >= 0.90, f"match rate too low: {rate:.1%}"

def test_confidence_scores_reasonable():
    df = pd.read_csv(os.path.join(DATA_DIR, "geocoded_results.csv"))
    scores = df["gc_score"].dropna()
    assert scores.mean() > 80, f"avg confidence too low: {scores.mean():.1f}"

def test_some_results_are_accurate():
    # At least some geocodes should be within 500m
    df = pd.read_csv(os.path.join(DATA_DIR, "geocoded_results.csv"))
    close = (df["distance_m"] <= 500).sum()
    assert close > 0, "no results within 500m — something is wrong"


# haversine sanity check

def test_haversine_known_distance():
    # Chicago loop to O'Hare is roughly 24 km
    from pipeline.geocode_pipeline import haversine
    dist = haversine(41.8781, -87.6298, 41.9742, -87.9073)
    assert 23000 < dist < 26000, f"haversine seems off: {dist:.0f}m"

def test_haversine_same_point_is_zero():
    from pipeline.geocode_pipeline import haversine
    dist = haversine(41.8781, -87.6298, 41.8781, -87.6298)
    assert dist < 1, f"same point should be ~0m, got {dist:.1f}m"
