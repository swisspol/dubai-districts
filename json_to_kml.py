#!/usr/bin/env python3
"""Convert dubai-map.json districts to a KML file."""

import json
import os
import sys
import xml.etree.ElementTree as ET
from xml.dom import minidom

INPUT = "dubai-map.json"
OUTPUT = "dubai-map.kml"


def hex_to_kml_color(hex_color, alpha="cc"):
    """Convert #RRGGBB to KML's AABBGGRR format."""
    assert hex_color.startswith("#") and len(hex_color) == 7, \
        f"Expected #RRGGBB color, got {hex_color!r}"
    h = hex_color.lstrip("#")
    r, g, b = h[0:2], h[2:4], h[4:6]
    return f"{alpha}{b}{g}{r}"


def build_polygon(parent, rings):
    assert rings, "Polygon has no rings"
    polygon = ET.SubElement(parent, "Polygon")
    outer = ET.SubElement(polygon, "outerBoundaryIs")
    lr = ET.SubElement(outer, "LinearRing")
    assert len(rings[0]) >= 3, "Outer ring has fewer than 3 points"
    ET.SubElement(lr, "coordinates").text = " ".join(
        f"{lon},{lat},0" for lon, lat in rings[0]
    )
    for ring in rings[1:]:
        assert len(ring) >= 3, "Inner ring has fewer than 3 points"
        inner = ET.SubElement(polygon, "innerBoundaryIs")
        lr = ET.SubElement(inner, "LinearRing")
        ET.SubElement(lr, "coordinates").text = " ".join(
            f"{lon},{lat},0" for lon, lat in ring
        )


def build_kml(items):
    assert items, "No items to process"
    kml = ET.Element("kml", xmlns="http://www.opengis.net/kml/2.2")
    doc = ET.SubElement(kml, "Document")
    ET.SubElement(doc, "name").text = "Dubai Districts"

    written = 0
    for item in items:
        name = item.get("name") or f"(id={item.get('id')})"
        raw_geom = item.get("geometry")
        if not raw_geom:
            continue

        geom = json.loads(raw_geom)
        assert geom.get("type") == "Polygon", \
            f"[{name}] unexpected geometry type: {geom.get('type')!r}"
        rings = geom.get("coordinates")
        assert rings, f"[{name}] geometry has no coordinates"

        pm = ET.SubElement(doc, "Placemark")
        ET.SubElement(pm, "name").text = item.get("name", "")

        color = item.get("color")
        if color:
            style = ET.SubElement(pm, "Style")
            poly_style = ET.SubElement(style, "PolyStyle")
            ET.SubElement(poly_style, "color").text = hex_to_kml_color(color)
            ET.SubElement(poly_style, "outline").text = "1"

        build_polygon(pm, rings)
        written += 1

    assert written > 0, "No placemarks were written — check geometry data"
    return kml, written


def pretty_print(element):
    rough = ET.tostring(element, encoding="unicode")
    return minidom.parseString(rough).toprettyxml(indent="  ")


def main():
    assert os.path.exists(INPUT), f"Input file not found: {INPUT}"

    with open(INPUT, encoding="utf-8") as f:
        data = json.load(f)

    assert "items" in data, "Expected top-level 'items' array in source JSON"
    items = data["items"]
    assert len(items) > 0, "Source JSON contains no items"
    print(f"Loaded {len(items)} districts")

    kml, written = build_kml(items)
    xml_str = pretty_print(kml)

    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(xml_str)

    print(f"Wrote {written} placemarks to {OUTPUT}")


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, ValueError, KeyError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
