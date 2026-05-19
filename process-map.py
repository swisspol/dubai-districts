#!/usr/bin/env python3
"""Extract districts from dubai-map.json and write docs/data.json as a GeoJSON FeatureCollection."""

import json
import os
import sys

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


def parse_label_point(raw_coords, item_name):
    parts = raw_coords.split(",")
    assert len(parts) == 2, \
        f"[{item_name}] expected 'lat, lon' but got {raw_coords!r}"
    lat, lon = float(parts[0].strip()), float(parts[1].strip())
    assert -90 <= lat <= 90, f"[{item_name}] lat out of range: {lat}"
    assert -180 <= lon <= 180, f"[{item_name}] lon out of range: {lon}"
    return [lon, lat]


def parse_geometry(raw_geom, item_name):
    geom = json.loads(raw_geom)
    assert geom.get("type") == "Polygon", \
        f"[{item_name}] unexpected geometry type: {geom.get('type')!r}"
    assert geom.get("coordinates"), f"[{item_name}] geometry has no coordinates"
    return geom


def main():
    assert os.path.exists(INPUT), f"Input file not found: {INPUT}"
    assert os.path.isdir(os.path.dirname(OUTPUT)), \
        f"Output directory does not exist: {os.path.dirname(OUTPUT)}"

    with open(INPUT, encoding="utf-8") as f:
        data = json.load(f)

    assert "items" in data, "Expected top-level 'items' array in source JSON"
    assert len(data["items"]) > 0, "Source JSON contains no items"

    features = []
    skipped = []

    for item in data["items"]:
        name = item.get("name") or f"(id={item.get('id')})"
        raw_geom = item.get("geometry")
        if not raw_geom:
            skipped.append(name)
            continue

        geometry = parse_geometry(raw_geom, name)

        properties = {
            "name": item.get("name", ""),
            "color": item.get("color", "#888888"),
        }

        assert properties["color"].startswith("#") and len(properties["color"]) == 7, \
            f"[{name}] unexpected color format: {properties['color']!r}"

        raw_coords = item.get("coordinates", "")
        if raw_coords:
            properties["label_lng"], properties["label_lat"] = parse_label_point(raw_coords, name)

        for field in STAT_FIELDS:
            val = item.get(field)
            if val is not None:
                properties[field] = val

        features.append({"type": "Feature", "properties": properties, "geometry": geometry})

    assert len(features) > 0, "No features produced — check geometry data"

    collection = {"type": "FeatureCollection", "features": features}

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(collection, f, separators=(",", ":"))

    if skipped:
        print(f"Skipped {len(skipped)} items with no geometry: {', '.join(skipped)}")
    print(f"Wrote {len(features)} features to {OUTPUT}")


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, ValueError, KeyError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
