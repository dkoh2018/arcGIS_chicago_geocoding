# Fetch chicago crime records from the city's open data portal (Socrata API)
# We need records with block-level addresses and known coordinates
# so we can compare against ArcGIS geocoding results later

import requests
import pandas as pd
import os

SOCRATA_ENDPOINT = "https://data.cityofchicago.org/resource/ijzp-q8t2.json"

# Grab recent crimes with valid addresses and coordinates
PARAMS = {
    "$limit": 600,  # extra buffer in case some rows have issues
    "$where": "latitude IS NOT NULL AND longitude IS NOT NULL AND block IS NOT NULL",
    "$order": "date DESC",
    "$select": "id,case_number,date,block,primary_type,description,location_description,latitude,longitude",
}


def fetch_crime_data(target_rows=500):
    resp = requests.get(SOCRATA_ENDPOINT, params=PARAMS, timeout=30)
    resp.raise_for_status()

    df = pd.DataFrame(resp.json())
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df = df.dropna(subset=["latitude", "longitude", "block"])

    return df.head(target_rows)


if __name__ == "__main__":
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    os.makedirs(data_dir, exist_ok=True)

    df = fetch_crime_data()
    df.to_csv(os.path.join(data_dir, "chicago_crimes_raw.csv"), index=False)

    # Quick check
    print(df.shape)
    print(df.head())
