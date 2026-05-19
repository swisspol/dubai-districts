#!/usr/bin/env python3
"""Convert dubai-map.json districts to a KML file."""

import json
import xml.etree.ElementTree as ET
from xml.dom import minidom

INPUT = "dubai-map.json"
OUTPUT = "dubai-map.kml"


def hex_to_kml_color(hex_color, alpha="cc"):
    """Convert #RRGGBB to KML's AABBGGRR format."""
    h = hex_color.lstrip("#")
    r, g, b = h[0:2], h[2:4], h[4:6]
    return f"{alpha}{b}{g}{r}"



def build_polygon(parent, rings):
    polygon = ET.SubElement(parent, "Polygon")
    outer = ET.SubElement(polygon, "outerBoundaryIs")
    lr = ET.SubElement(outer, "LinearRing")
    ET.SubElement(lr, "coordinates").text = " ".join(
        f"{lon},{lat},0" for lon, lat in rings[0]
    )
    for ring in rings[1:]:
        inner = ET.SubElement(polygon, "innerBoundaryIs")
        lr = ET.SubElement(inner, "LinearRing")
        ET.SubElement(lr, "coordinates").text = " ".join(
            f"{lon},{lat},0" for lon, lat in ring
        )


def build_kml(items):
    kml = ET.Element("kml", xmlns="http://www.opengis.net/kml/2.2")
    doc = ET.SubElement(kml, "Document")
    ET.SubElement(doc, "name").text = "Dubai Districts"

    for item in items:
        raw_geom = item.get("geometry")
        if not raw_geom:
            continue

        geom = json.loads(raw_geom)
        if geom["type"] != "Polygon":
            continue

        rings = geom["coordinates"]

        pm = ET.SubElement(doc, "Placemark")
        ET.SubElement(pm, "name").text = item.get("name", "")

        color = item.get("color")
        if color:
            style = ET.SubElement(pm, "Style")
            poly_style = ET.SubElement(style, "PolyStyle")
            ET.SubElement(poly_style, "color").text = hex_to_kml_color(color)
            ET.SubElement(poly_style, "outline").text = "1"

        build_polygon(pm, rings)

    return kml


def pretty_print(element):
    rough = ET.tostring(element, encoding="unicode")
    return minidom.parseString(rough).toprettyxml(indent="  ")


def main():
    with open(INPUT, encoding="utf-8") as f:
        data = json.load(f)

    items = data["items"]
    print(f"Loaded {len(items)} districts")

    kml = build_kml(items)

    xml_str = pretty_print(kml)
    # minidom adds an XML declaration; keep it
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(xml_str)

    written = sum(1 for it in items if it.get("geometry"))
    print(f"Wrote {written} placemarks to {OUTPUT}")


if __name__ == "__main__":
    main()
