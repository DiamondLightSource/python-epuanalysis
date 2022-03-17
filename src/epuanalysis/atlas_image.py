from pathlib import Path
from PIL import Image

from math import sqrt
from typing import Optional, Tuple
from skimage import segmentation, img_as_float

import numpy as np

from epuanalysis.scale import ImageScale


def construct_atlas(
    tile_dir: Path,
    detector_dimensions: Optional[Tuple[int, int]] = None,
    grid: bool = True,
    figfile: Path = Path("./EPU_analysis/atlas.jpg"),
) -> ImageScale:
    tile_images = tile_dir.glob("Tile*.jpg")
    tiles = [
        ImageScale(ti, detector_dimensions=detector_dimensions) for ti in tile_images
    ]
    for t in tiles:
        t.retrieve_xml_data()
    atlas_size_x = tiles[0].xextent
    atlas_size_y = tiles[0].yextent
    atlas = Image.new(mode="RGB", size=(atlas_size_x, atlas_size_y))
    left = min(sc.cx - 0.5 * sc.spacing * sc.xextent for sc in tiles)
    right = max(sc.cx + 0.5 * sc.spacing * sc.xextent for sc in tiles)
    bottom = min(sc.cy - 0.5 * sc.spacing * sc.yextent for sc in tiles)
    top = max(sc.cy + 0.5 * sc.spacing * sc.yextent for sc in tiles)
    new_spacing = (right - left) / atlas_size_x
    for t in tiles:
        upper_left_pix_x = (
            int(-(t.upper_left[0] - (left + (right - left) / 2)) / new_spacing)
            + atlas_size_x // 2
        )
        upper_left_pix_y = (
            int((t.upper_left[1] - (bottom + (top - bottom) / 2)) / new_spacing)
            + atlas_size_y // 2
        )

        if grid:
            shiftx = int(upper_left_pix_x % (t.xextent / sqrt(len(tiles))))
            shifty = int(upper_left_pix_y % (t.yextent / sqrt(len(tiles))))
            if shiftx < (t.xextent / sqrt(len(tiles)) / 2):
                if upper_left_pix_x >= 0:
                    upper_left_pix_x -= shiftx
                else:
                    upper_left_pix_x += shiftx
            else:
                if upper_left_pix_x >= 0:
                    upper_left_pix_x += int(t.xextent / sqrt(len(tiles)) - shiftx)
                else:
                    upper_left_pix_x -= int(t.xextent / sqrt(len(tiles)) - shiftx)
            if shifty < (t.yextent / sqrt(len(tiles)) / 2):
                if upper_left_pix_y >= 0:
                    upper_left_pix_y -= shifty
                else:
                    upper_left_pix_y += shifty
            else:
                if upper_left_pix_y >= 0:
                    upper_left_pix_y += int(t.yextent / sqrt(len(tiles)) - shifty)
                else:
                    upper_left_pix_y -= int(t.yextent / sqrt(len(tiles)) - shifty)

        with Image.open(t.image) as im:
            im.thumbnail((t.xextent / sqrt(len(tiles)), t.yextent / sqrt(len(tiles))))
            atlas.paste(im, (upper_left_pix_x, upper_left_pix_y))
    atlas.save(figfile)
    atlas_scale = ImageScale(
        figfile,
        spacing=new_spacing,
        centre=(left + (right - left) / 2, bottom + (top - bottom) / 2),
    )
    return atlas_scale
