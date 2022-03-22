from __future__ import annotations

import mrcfile
import xml.etree.ElementTree as ET

from functools import lru_cache
from pathlib import Path
from PIL import Image, ImageDraw

from typing import Any, Dict, Optional, Tuple


class ImageScale:
    def __init__(
        self,
        image_path: Path,
        name: str = "",
        spacing: Optional[float] = None,
        centre: Optional[Tuple[float, float]] = None,
        detector_dimensions: Optional[Tuple[int, int]] = None,
        above: Optional[Dict[Any, ImageScale]] = None,
        below: Optional[Dict[Any, ImageScale]] = None,
    ):
        self.name = name or image_path

        self.above = {}
        if above:
            self.above.update(above)
            for sc in self.above.values():
                sc.below.update({image_path: self})

        self.below = {}
        if below:
            self.below.update(below)
            for sc in self.below.values():
                sc.above.update({image_path: self})

        self.image = image_path
        with Image.open(self.image) as im:
            self.xextent = im.size[0]
            self.yextent = im.size[1]
        if not detector_dimensions:
            try:
                with mrcfile.open(self.image.with_suffix(".mrc")) as im:
                    detector_dimensions = im.data.shape
            except FileNotFoundError:
                detector_dimensions = (self.xextent, self.yextent)
        self._detector_dimensions = detector_dimensions
        if spacing and centre:
            self.spacing = spacing * (detector_dimensions[0] / self.xextent)
            self.cx = centre[0]
            self.cy = centre[1]
        else:
            self.retrieve_xml_data()
        self.pcx: int = self.xextent // 2
        self.pcy: int = self.yextent // 2

    @property
    def upper_left(self) -> Tuple[float, float]:
        return (
            self.cx + 0.5 * self.spacing * self.xextent,
            self.cy - 0.5 * self.spacing * self.yextent,
        )

    @property
    def upper_right(self) -> Tuple[float, float]:
        return (
            self.cx - 0.5 * self.spacing * self.xextent,
            self.cy - 0.5 * self.spacing * self.yextent,
        )

    @property
    def lower_right(self) -> Tuple[float, float]:
        return (
            self.cx - 0.5 * self.spacing * self.xextent,
            self.cy + 0.5 * self.spacing * self.yextent,
        )

    @property
    @lru_cache(maxsize=1)
    def pil_image(self):
        return Image.open(self.image)

    def add_below(self, below: Dict[Any, ImageScale]):
        self.below.update(below)
        for sc in below.values():
            sc.above.update({self.image: self})

    def add_above(self, above: Dict[Any, ImageScale]):
        self.above.update(above)
        for sc in above.values():
            sc.below.update({self.image: self})

    # @lru_cache(maxsize=1)
    def retrieve_xml_data(self):
        ns = {
            "p": "http://schemas.datacontract.org/2004/07/Applications.Epu.Persistence",
            "system": "http://schemas.datacontract.org/2004/07/System",
            "so": "http://schemas.datacontract.org/2004/07/Fei.SharedObjects",
            "g": "http://schemas.datacontract.org/2004/07/System.Collections.Generic",
            "s": "http://schemas.datacontract.org/2004/07/Fei.Applications.Common.Services",
            "a": "http://schemas.datacontract.org/2004/07/System.Drawing",
        }
        xml_path = self.image.with_suffix(".xml")
        tree = ET.parse(xml_path)
        root = tree.getroot()

        stage_position_X = root.find(
            "so:microscopeData/so:stage/so:Position/so:X", ns
        ).text
        stage_position_Y = root.find(
            "so:microscopeData/so:stage/so:Position/so:Y", ns
        ).text

        pixel_size = root.find(
            "so:SpatialScale/so:pixelSize/so:x/so:numericValue", ns
        ).text

        self.spacing = float(pixel_size) * (self._detector_dimensions[0] / self.xextent)
        self.cx = float(stage_position_X)
        self.cy = float(stage_position_Y)

    def get_pixel(self, coords: Tuple[float, float]) -> Tuple[int, int]:
        xpix = (-coords[0] + self.cx) // self.spacing
        ypix = (coords[1] - self.cy) // self.spacing
        return (xpix + self.pcx, ypix + self.pcy)

    def get_physical(self, pix_coords: Tuple[int, int]) -> Tuple[float, float]:
        x = self.cx + self.spacing * (self.pcx - pix_coords[0])
        y = self.cy + self.spacing * (pix_coords[1] - self.pcy)
        return (x, y)

    def mark_image(
        self,
        coords: Tuple[float, float],
        scale_shift: int = 0,
        target_tag: Any = None,
        show: bool = False,
    ) -> Image.Image:
        if not scale_shift:
            scale = self
        elif scale_shift > 0:
            scale = self
            for i in range(scale_shift):
                if len(scale.above) == 1:
                    scale = list(scale.above.values())[0]
                else:
                    scale = scale.above[target_tag]
        elif scale_shift < 0:
            scale = self
            for i in range(abs(scale_shift)):
                if len(scale.below) == 1:
                    scale = list(scale.below.values())[0]
                else:
                    scale = scale.below[target_tag]
        pix_coords = scale.get_pixel(coords)
        with Image.open(scale.image) as im:
            im.convert("RGB")
            d = ImageDraw.Draw(im)
            circle_size = int(0.015 * scale.xextent)
            d.ellipse(
                [
                    (pix_coords[0] - circle_size, pix_coords[1] - circle_size),
                    (pix_coords[0] + circle_size, pix_coords[1] + circle_size),
                ],
                outline="red",
                width=2,
            )
            if show:
                im.show()
            return im

    def is_in(self, other_scale: ImageScale) -> bool:
        px, py = other_scale.get_pixel((self.cx, self.cy))
        if px < 0 or py < 0:
            return False
        if px > other_scale.xextent or py > other_scale.yextent:
            return False
        return True
