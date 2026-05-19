# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Regenerate docs/data.json from the source data
python3 process-map.py

# Serve the map at http://localhost:8080
python3 serve.py
```

## Architecture

The pipeline runs in two stages:

1. **Data processing** (`process-map.py`) — reads `dubai-map.json` (165 Dubai districts) and writes `docs/data.json`, a GeoJSON FeatureCollection. Each feature carries `name`, `color` (`#RRGGBB`), and real-estate stat fields. The `geometry` field in the source is a JSON-encoded string and must be parsed with `json.loads()` per item.

2. **Frontend** (`docs/index.html`) — a single-file map viewer with no build step. Loads MapTiler SDK from CDN. At startup it fetches the `dataviz-v4` style JSON, strips all `symbol` layers to remove labels, then initialises the map. On load it adds a hillshade raster layer, then the district GeoJSON (`data.json`) as fill + outline layers using each feature's `color` property. Hover state is tracked via MapLibre feature-state for opacity highlighting.

## Key data facts

- `dubai-map.json` → `items[]` array; `geometry` is a **JSON string**, not an object.
- All geometries are `Polygon` (no MultiPolygon).
- One item has no geometry and is skipped by `process-map.py`.
- KML color format is `AABBGGRR` (reversed from HTML); `data.json` uses plain `#RRGGBB` so no conversion is needed in the frontend.
- `docs/data.json` is a build artifact — regenerate it after changing `dubai-map.json` or `process-map.py`.
