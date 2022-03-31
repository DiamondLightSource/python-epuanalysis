from __future__ import annotations

import mrcfile
import xmltodict

from functools import lru_cache
from pathlib import Path
from PIL import Image, ImageDraw

from typing import Any, Dict, Optional, Tuple

# from epuanalysis.frame import GUIFrame


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
        frame = None,
        flip: Tuple[bool, bool] = (False, False),
    ):
        self.name = name or image_path

        self._frame = frame

        self._flip = flip

        self.above = {}
        if above:
            self.above.update(above)
            for sc in self.above.values():
                sc.below.update({self.name: self})

        self.below = {}
        if below:
            self.below.update(below)
            for sc in self.below.values():
                sc.above.update({self.name: self})

        self.image = image_path
        with Image.open(self.image) as im:
            self.xextent = im.size[0]
            self.yextent = im.size[1]
        
        if spacing and centre and detector_dimensions:
            self._detector_dimensions = detector_dimensions
            self.spacing = spacing * (detector_dimensions[0] / self.xextent)
            self.cx = centre[0]
            self.cy = centre[1]
        else:
            xd = self.retrieve_xml_data()
            if not detector_dimensions:
                readoutarea = xd["microscopeData"]["acquisition"]["camera"]["ReadoutArea"]
                detector_dimensions = (int(readoutarea["a:width"]), int(readoutarea["a:height"]))
            self._detector_dimensions = detector_dimensions
            self.spacing = float(xd["SpatialScale"]["pixelSize"]["x"]["numericValue"]) * (self._detector_dimensions[0] / self.xextent)
            self.cx = float(xd["microscopeData"]["stage"]["Position"]["X"])
            self.cy = float(xd["microscopeData"]["stage"]["Position"]["Y"])
        
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
    def pil_image(self) -> Image.Image:
        if not self._flip:
            im = Image.open(self.image)
            return im.convert("RGBA")
        im = Image.open(self.image)
        if self._flip[0]:
            im = im.transpose(Image.FLIP_LEFT_RIGHT)
        if self._flip[1]:
            im = im.transpose(Image.FLIP_TOP_BOTTOM)
        return im.convert("RGBA")

    def add_below(self, below: Dict[Any, ImageScale]):
        self.below.update(below)
        for sc in below.values():
            sc.above.update({self.name: self})

    def add_above(self, above: Dict[Any, ImageScale]):
        self.above.update(above)
        for sc in above.values():
            sc.below.update({self.name: self})

    @lru_cache(maxsize=1)
    def retrieve_xml_data(self) -> dict:
        with open(self.image.with_suffix(".xml"), "r") as xf:
            content = xf.read()
            xd = xmltodict.parse(content)["MicroscopeImage"]
        return xd

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
        with scale.pil_image as im:
            im.convert("RGB")
            d = ImageDraw.Draw(im)

            half_square_width = int(0.5*(self.spacing/scale.spacing) * self.xextent)

            ulx = (-pix_coords[0] + half_square_width + scale.xextent) if scale._flip[0] else pix_coords[0] - half_square_width
            uly = (-pix_coords[1] + half_square_width + scale.yextent) if scale._flip[1] else pix_coords[1] - half_square_width
            upper_left = (ulx, uly)
            lrx = (-pix_coords[0] - half_square_width + scale.xextent) if scale._flip[0] else pix_coords[0] + half_square_width
            lry = (-pix_coords[1] - half_square_width + scale.yextent) if scale._flip[1] else pix_coords[1] + half_square_width
            lower_right = (lrx, lry)
          
            d.rectangle(
                [upper_left, lower_right],
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
