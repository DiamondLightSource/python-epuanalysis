from __future__ import annotations

import mrcfile
import numpy as np
import starfile
from pathlib import Path
from pandas import DataFrame
from PIL import Image

from typing import Dict, List, Optional

from epuanalysis.scale import ImageScale

class ImageDistribution:
    def __init__(self, name: str, img: ImageScale, data: Optional[np.array] = None):
        self._name = name 
        self._img = img
        self._data = data or np.zeros((self._img.xextent, self._img.yextent))

    def __sub__(self, other: ImageDistribution) -> ImageDistribution:
        if self._img.image != other._img.image:
            raise ValueError(f"To calculate the different of two ImageDistributions they must have the same base image: {self._img.image} != {other._img.image}")
        new_name = f"{self._name} - {other._name}"
        new_data = np.subtract(self._data, other._data)
        return ImageDistribution(new_name, self._img, data=new_data)

    def from_mrc(self, mrc_path: Path):
        with mrcfile.open(mrc_path) as mrc:
            data = mrc.data 
        if not len(data.shape) == 2:
            raise ValueError(f"mrc files passed to an ImageDistribution must have shape (n, m) not {data.shape}")
        if (data.shape[0], data.shape[1]) != (self._img.xextent, self._img.yextent):
            with Image.fromarray(data) as im:
                im.thumbnail((self._img.xextent, self._img.yextent))
                data = np.array(im)
        self._data = data

    def from_particles(self, part_coords: List[Tuple[int, int]], data: List[float], diameter: float):
        scale_factor = (self._img.xextent/self._img._detector_dimensions[0], self._img.yextent/self._img._detector_dimensions[1])
        for coord, d in zip(part_coords, data):
            left = int(coord[0]*scale_factor[0] - 0.5*diameter)
            right = int(coord[1]*scale_factor[1] + 0.5*diameter)
            bottom = int(coord[1]*scale_factor[1] - 0.5*diameter)
            top = int(coord[1]*scale_factor[1] + 0.5*diameter)
            # probably really slow
            for i in range(left, right):
                for j in range(bottom, top):
                    curr = self._data[i][j]
                    self._data[i][j] = 0.5*(curr + d) if curr else d

    def from_star(self, star_file: Path, column: str, diameter: float):
        def _get_df(_df: Dict[str, DataFrame]) -> DataFrame:
            for v in _df.values():
                if "rlnCoordinateX" in v.columns:
                    return v

        df = _get_df(starfile.read(star_file))
        # this_df = df[df["rlnMicrographName"].isin(str(self._img.image))]
        this_df = df[df["rlnMicrographName"].str.contains(self._img.image.stem)]
        part_coords = []
        data = []
        for i, row in this_df.iterrows():
            part_coords.append((row["rlnCoordinateX"], row["rlnCoordinateY"]))
            data.append(row[column])
        self.from_particles(part_coords, data, diameter)
