import os
import matplotlib
import matplotlib.pyplot as plt

from pathlib import Path
from gemmi import cif
from typing import Tuple, List


def plot_coords(
    starfile: Path,
    micrograph: Path,
    x: int,
    y: int,
    diameter: float,
    outdir: Path,
    flip: Tuple[bool, bool] = (False, False),
):
    gemmi_readable = os.fspath(starfile)
    star_doc = cif.read_file(gemmi_readable)

    def _get_coords(star_document) -> List[Tuple[float, float]]:
        _coords = []
        for block in star_document:
            mics = list(block.find_loop("_rlnMicrographName"))
            xcol = list(block.find_loop("_rlnCoordinateX"))
            if xcol:
                ycol = list(block.find_loop("_rlnCoordinateY"))
                _coords = [(float(_x), float(_y)) for _x, _y, m in zip(xcol, ycol, mics) if micrograph.stem in m]
                return _coords
        return _coords

    coords = _get_coords(star_doc)
    fig = plt.figure(figsize=(1024 / 100.0, 1024 / 100.0), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim([0, x])
    ax.set_ylim([0, y])
    if flip[0]:
        ax.invert_xaxis()
    if flip[1]:
        ax.invert_yaxis()
    for xc, yc in coords:
        circ = plt.Circle((xc, yc), diameter, fill=False, color="orange")
        ax.add_patch(circ)

    fig.savefig(outdir / "particles.png", transparent=True)
