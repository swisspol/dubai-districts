#!/usr/bin/env python3
"""Extract districts from dubai-map.json and write docs/data.json as a GeoJSON FeatureCollection."""

import json
import os
import sys

INPUT = os.path.join(os.path.dirname(__file__), "dubai-map.json")
OUTPUT = os.path.join(os.path.dirname(__file__), "docs", "data.json")

COLOR_PALETTE = [
    "#FFB3BA", "#FFD9A0", "#FFFACD",
    "#B5EAD7", "#A8D8EA", "#C9B8F0",
    "#F5A5C8", "#C7F2A4", "#F5CBA5",
]

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


def _pt_to_seg_dist_sq(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return (px - ax) ** 2 + (py - ay) ** 2
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return (px - ax - t * dx) ** 2 + (py - ay - t * dy) ** 2


def _rings_adjacent(ring_a, ring_b, eps_sq):
    """True if any vertex of ring_a is within sqrt(eps_sq) of an edge of ring_b, or vice versa."""
    for px, py in ring_a:
        for k in range(len(ring_b) - 1):
            if _pt_to_seg_dist_sq(px, py, *ring_b[k], *ring_b[k + 1]) <= eps_sq:
                return True
    for px, py in ring_b:
        for k in range(len(ring_a) - 1):
            if _pt_to_seg_dist_sq(px, py, *ring_a[k], *ring_a[k + 1]) <= eps_sq:
                return True
    return False


def build_adjacency(features):
    """Return adjacency list using vertex-to-edge proximity.

    Adjacent polygons in this dataset are independently digitised and don't
    share exact vertices — boundaries fall within ~2m of each other. We use
    a 50m (~0.0005 deg) tolerance to robustly detect shared edges while
    avoiding false positives between non-touching districts.
    """
    EPS = 0.0005          # ~55 m in degrees
    EPS_SQ = EPS * EPS

    rings = [f["geometry"]["coordinates"][0] for f in features]

    # Bounding boxes for pre-filtering
    def bbox(ring):
        xs = [p[0] for p in ring]
        ys = [p[1] for p in ring]
        return min(xs), min(ys), max(xs), max(ys)

    boxes = [bbox(r) for r in rings]

    n = len(features)
    adjacency = [set() for _ in range(n)]
    for i in range(n):
        x0, y0, x1, y1 = boxes[i]
        for j in range(i + 1, n):
            x0j, y0j, x1j, y1j = boxes[j]
            # Skip pairs whose bounding boxes are far apart
            if x0j > x1 + EPS or x1j < x0 - EPS or y0j > y1 + EPS or y1j < y0 - EPS:
                continue
            if _rings_adjacent(rings[i], rings[j], EPS_SQ):
                adjacency[i].add(j)
                adjacency[j].add(i)
    return adjacency


def greedy_color(adjacency, palette):
    """Assign palette indices so no two adjacent nodes share a color."""
    n = len(adjacency)
    assigned = [-1] * n
    order = sorted(range(n), key=lambda i: len(adjacency[i]), reverse=True)
    for i in order:
        used = {assigned[j] for j in adjacency[i] if assigned[j] != -1}
        for c in range(len(palette)):
            if c not in used:
                assigned[i] = c
                break
        else:
            assigned[i] = 0
    return assigned


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
    props_list = []

    for item in data["items"]:
        name = item.get("name") or f"(id={item.get('id')})"
        raw_geom = item.get("geometry")
        if not raw_geom:
            skipped.append(name)
            continue

        geometry = parse_geometry(raw_geom, name)
        properties = {"name": item.get("name", "")}

        raw_coords = item.get("coordinates", "")
        if raw_coords:
            properties["label_lng"], properties["label_lat"] = parse_label_point(raw_coords, name)

        for field in STAT_FIELDS:
            val = item.get(field)
            if val is not None:
                properties[field] = val

        features.append({"type": "Feature", "properties": properties, "geometry": geometry})

    assert len(features) > 0, "No features produced — check geometry data"

    adjacency = build_adjacency(features)
    color_assignments = greedy_color(adjacency, COLOR_PALETTE)
    for feature, color_idx in zip(features, color_assignments):
        feature["properties"]["color"] = COLOR_PALETTE[color_idx]

    collection = {"type": "FeatureCollection", "features": features}

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(collection, f, separators=(",", ":"))

    if skipped:
        print(f"Skipped {len(skipped)} items with no geometry: {', '.join(skipped)}")
    print(f"Wrote {len(features)} features to {OUTPUT}")

    # Validate: no two adjacent districts share the same color
    conflicts = [
        (features[i]["properties"]["name"], features[j]["properties"]["name"],
         features[i]["properties"]["color"])
        for i in range(len(features))
        for j in adjacency[i]
        if j > i and features[i]["properties"]["color"] == features[j]["properties"]["color"]
    ]
    if conflicts:
        for a, b, color in conflicts:
            print(f"  COLOR CONFLICT: '{a}' and '{b}' both have {color}", file=sys.stderr)
        raise AssertionError(f"{len(conflicts)} color conflict(s) found")
    total_edges = sum(len(a) for a in adjacency) // 2
    print(f"Validation passed: {total_edges} adjacencies, 0 color conflicts")


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, ValueError, KeyError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
