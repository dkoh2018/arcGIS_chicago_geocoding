# Batch geocode chicago crime addresses through ArcGIS
# and compare against known coordinates to measure accuracy

import pandas as pd
import os
from math import radians, sin, cos, sqrt, atan2
from arcgis.gis import GIS
from arcgis.geocoding import geocode


def haversine(lat1, lon1, lat2, lon2):
    # Calculate distance between two coordinates in meters
    R = 6371000
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1-a))


def geocode_address(address, city="Chicago", state="IL"):
    # Try to geocode a single address through ArcGIS
    try:
        full_addr = f"{address}, {city}, {state}"
        results = geocode(full_addr, max_locations=1)
        if results:
            r = results[0]
            return {
                "gc_address": r["address"],
                "gc_score": r["score"],
                "gc_lat": r["location"]["y"],
                "gc_lng": r["location"]["x"],
            }
    except Exception as e:
        print(f"failed on: {address} ({e})")
    return None


def run_geocoding_pipeline(input_csv, output_csv):
    df = pd.read_csv(input_csv)

    # Connect anonymously - no API key needed for basic geocoding
    gis = GIS()

    results = []
    for i, row in df.iterrows():
        result = geocode_address(row["block"])

        if result:
            # How far off was the geocoded result from the known location?
            result["distance_m"] = haversine(
                row["latitude"], row["longitude"],
                result["gc_lat"], result["gc_lng"]
            )
        else:
            result = {"gc_address": None, "gc_score": None,
                      "gc_lat": None, "gc_lng": None, "distance_m": None}

        results.append(result)

        if (i + 1) % 50 == 0:
            print(f"  {i + 1}/{len(df)}")

    # Combine original data with geocoding results
    gc_df = pd.DataFrame(results)
    out = pd.concat([df, gc_df], axis=1)
    out.to_csv(output_csv, index=False)

    # Quick summary
    matched = out["gc_score"].notna().sum()
    print(f"matched: {matched}/{len(out)}")
    print(f"median error: {out['distance_m'].median():.0f}m")
    print(f"mean score: {out['gc_score'].mean():.1f}")

    return out


if __name__ == "__main__":
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    run_geocoding_pipeline(
        os.path.join(data_dir, "chicago_crimes_raw.csv"),
        os.path.join(data_dir, "geocoded_results.csv")
    )
