from xml.dom import minidom


class SVGImage:
    _svg: minidom.Element

    def __init__(self, svg_string: str):
        parsed = minidom.parseString(svg_string)
        self._svg = parsed.getElementsByTagName("svg")[0]

    @property
    def width(self) -> int:
        return int(self._svg.getAttribute("width"))

    @property
    def height(self) -> int:
        return int(self._svg.getAttribute("height"))
