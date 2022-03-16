import pathlib
import xml.etree.ElementTree as ET

from typing import NamedTuple


class PlanePosition(NamedTuple):
    x: float
    y: float


def parse_atlas_xml(xml_path: pathlib.Path) -> dict:
    ns = {
        "p": "http://schemas.datacontract.org/2004/07/Applications.Epu.Persistence",
        "system": "http://schemas.datacontract.org/2004/07/System",
        "so": "http://schemas.datacontract.org/2004/07/Fei.SharedObjects",
        "g": "http://schemas.datacontract.org/2004/07/System.Collections.Generic",
        "s": "http://schemas.datacontract.org/2004/07/Fei.Applications.Common.Services",
        "a": "http://schemas.datacontract.org/2004/07/System.Drawing",
    }
    tree = ET.parse(xml_path)
    root = tree.getroot()

    stage_position_A = root.find("so:microscopeData/so:stage/so:Position/so:A", ns).text
    stage_position_B = root.find("so:microscopeData/so:stage/so:Position/so:B", ns).text
    stage_position_X = root.find("so:microscopeData/so:stage/so:Position/so:X", ns).text
    stage_position_Y = root.find("so:microscopeData/so:stage/so:Position/so:Y", ns).text
    stage_position_Z = root.find("so:microscopeData/so:stage/so:Position/so:Z", ns).text

    pixel_size = root.find("so:SpatialScale/so:pixelSize/so:x/so:numericValue", ns).text

    return {
        "stage_position": PlanePosition(stage_position_X, stage_position_Y),
        "pixel_size": pixel_size,
    }
