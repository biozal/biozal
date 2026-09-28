import xml.etree.ElementTree as ET

SVG_NS = "{http://www.w3.org/2000/svg}"


def assert_valid_svg(svg: str) -> ET.Element:
    root = ET.fromstring(svg)
    assert root.tag == f"{SVG_NS}svg"
    assert root.get("viewBox"), "svg must have a viewBox"
    assert root.get("shape-rendering") == "crispEdges"
    return root
