#!/usr/bin/env python3
"""Extract districts from dubai-map.json and write docs/data.json as a GeoJSON FeatureCollection."""

import json
import os

INPUT = os.path.join(os.path.dirname(__file__), "dubai-map.json")
OUTPUT = os.path.join(os.path.dirname(__file__), "docs", "data.json")

STAT_FIELDS = [
    "supply",
    "sales_volume",
    "median_price_sqft",
    "rental_yield",
    "capital_appreciation",
    "new_project_count",
    "new_unit_count",
    "sales_volume_first_sale",
    "sales_volume_re_sale",
]


def main():
    with open(INPUT, encoding="utf-8") as f:
        data = json.load(f)

    features = []
    skipped = 0

    for item in data["items"]:
        raw_geom = item.get("geometry")
        if not raw_geom:
            skipped += 1
            continue

        geometry = json.loads(raw_geom)

        properties = {
            "name": item.get("name", ""),
            "color": item.get("color", "#888888"),
        }
        for field in STAT_FIELDS:
            val = item.get(field)
            if val is not None:
                properties[field] = val

        features.append({
            "type": "Feature",
            "properties": properties,
            "geometry": geometry,
        })

    collection = {"type": "FeatureCollection", "features": features}

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(collection, f, separators=(",", ":"))

    print(f"Wrote {len(features)} features to {OUTPUT} ({skipped} skipped)")


if __name__ == "__main__":
    main()
