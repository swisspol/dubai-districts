# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Regenerate docs/data.json from the source data
python3 process-map.py

# Regenerate dubai-map.kml from the source data
python3 json_to_kml.py

# Serve the map at http://localhost:8080
python3 serve.py
```

## Architecture

The pipeline runs in two stages:

1. **Data processing** (`process-map.py`) — reads `dubai-map.json` (165 Dubai districts) and writes `docs/data.json`, a GeoJSON FeatureCollection. Each feature carries `name`, `color` (`#RRGGBB`), `label_lng`/`label_lat` (the district's designated label point), and real-estate stat fields. The `geometry` field in the source is a JSON-encoded string and must be parsed with `json.loads()` per item.

2. **Frontend** (`docs/index.html`) — single-file map viewer, no build step. Loads MapTiler SDK from CDN. At startup it fetches the `dataviz-v4` style JSON, strips all `symbol` layers to suppress basemap labels, then initialises the map. On load it adds a hillshade raster layer (`api.maptiler.com/tiles/hillshade`), the district polygons from `data.json` as fill + outline layers coloured by each feature's `color` property, and a symbol layer that places district name labels at `label_lng`/`label_lat`.

`json_to_kml.py` is a separate export tool that writes `dubai-map.kml` (not used by the frontend).

## Key data facts

- `dubai-map.json` → `items[]` array; `geometry` is a **JSON string**, not an object — parse with `json.loads()`.
- `coordinates` field is `"lat, lon"` (reversed from GeoJSON); `process-map.py` flips it to `[lon, lat]`.
- All geometries are `Polygon` (no MultiPolygon).
- `Al Yelayiss 1` has no geometry and is skipped by both scripts.
- KML color format is `AABBGGRR` (reversed from HTML `#RRGGBB`); `data.json` keeps plain `#RRGGBB` so no conversion is needed in the frontend.
- `docs/data.json` is a build artifact — regenerate it after changing `dubai-map.json` or `process-map.py`.

## Error handling conventions

Both Python scripts use `assert` for invariant checks (schema, geometry type, coordinate ranges, color format) and catch `AssertionError`/`ValueError`/`KeyError` at the top level, printing to stderr and exiting with code 1.
