import functools
import os
import pathlib
from collections import Counter
from typing import Dict, List, NamedTuple, Set, Optional, Tuple

from gemmi import cif


class Micrograph(NamedTuple):
    name: pathlib.Path
    grid_square: str
    foil_hole: str
    num_particles: Optional[int]


class FoilHole(NamedTuple):
    name: str
    foil_hole_img: pathlib.Path
    exposures: List[Tuple[pathlib.Path, int]]


class GridSquare(NamedTuple):
    name: str
    grid_square_img: pathlib.Path
    foil_holes: List[FoilHole]


class EPUTracker:
    def __init__(
        self,
        basepath: pathlib.Path,
        epudir: pathlib.Path,
        suffix: str = "",
        starfile: Optional[pathlib.Path] = None,
        column: str = "",
        atlas: str = "",
    ):
        self.basepath = basepath
        self.epudir = epudir
        self.suffix = suffix
        self.starfile = starfile
        self.column = column
        self.atlas = atlas
        self.outdir = self.basepath / "EPU_analysis"
        self.counted_micrographs = Counter([])
     
        self.outdir.mkdir(exist_ok=True)
        self.settings = self.basepath / "EPU_analysis" / "settings.dat"
        self.epuout = self.basepath / "EPU_analysis"
        self.star_dir = self.basepath / "EPU_analysis" / "star"
        # save settings to disk
        with self.settings.open("w") as sf:
            sf.write("Tracking settings\n")
            if self.starfile:
                sf.write(f"Star: {self.basepath / self.starfile}\n")
            sf.write(f"EPU: {self.epudir}\n")
            sf.write(f"Column: {self.column}\n")
            sf.write(f"Suffix: {self.suffix}\n")
            sf.write(f"Atlas: {self.atlas}\n")
        # (self.outdir / "star").mkdir()

    @staticmethod
    def _get_gs(mic: pathlib.Path) -> str:
        for p in mic.parts:
            if "GridSquare" in p:
                split_name = p.split("_")
                i = split_name.index("GridSquare")
                return split_name[i] + "_" + split_name[i + 1]
        return ""

    @staticmethod
    def _get_fh(mic: pathlib.Path) -> str:
        split_name = mic.stem.split("_")
        i = split_name.index("FoilHole")
        return split_name[i + 1]

    def extract(self, starfile: pathlib.Path) -> Set[Micrograph]:
        gemmi_readable = os.fspath(starfile)
        star_doc = cif.read_file(gemmi_readable)
        column_data: List[pathlib.Path] = []
        _coords = False
        if "_rlnCoordinate" in self.column:
            _coords = True
        for block in star_doc:
            col = list(block.find_loop(self.column))
            if not _coords:
                coord_check = list(block.find_loop("_rlnCoordinateX"))
                _coords = bool(coord_check)
            if col:
                column_data = [pathlib.Path(c) for c in col]
                break
        mics = [mic for mic in column_data if str(mic).endswith(self.suffix)]
        unique_paths = set(mics)
        self.counted_micrographs = Counter([mic.stem for mic in mics])
        unique_mics = {
            Micrograph(
                mic,
                self._get_gs(mic),
                self._get_fh(mic),
                self.counted_micrographs[mic.stem] if _coords else None,
            )
            for mic in unique_paths
        }
        return unique_mics

    @property
    @functools.lru_cache(maxsize=1)
    def epu_images(self) -> Dict[str, GridSquare]:
        structured_imgs = {}
        gridsquare_dirs = [p for p in self.epudir.glob("GridSquare*")]
        for gsd in gridsquare_dirs:
            if not gsd.is_dir():
                continue
            foilholes = [p for p in (gsd / "FoilHoles").glob("FoilHole*.jpg")]
            fh_data = {}
            for fh in foilholes:
                fh_name = "_".join(fh.stem.split("_")[:2])
                exposures = []
                for p in (gsd / "Data").glob("*.jpg"):
                    if fh_name in p.name:
                        num_parts = 0
                        for cmic, np in self.counted_micrographs.items():
                            if p.stem in cmic:
                                num_parts = np
                                break
                        exposures.append((p, num_parts))
                if fh_data.get(fh_name):
                    if fh_data[fh_name].foil_hole_img.stat().st_mtime > fh.stat().st_mtime:
                        continue
                fh_data[fh_name] = FoilHole(
                    fh_name,
                    fh,
                    exposures,
                )
            structured_imgs[gsd.stem] = GridSquare(
                gsd.stem, list(gsd.glob("*.jpg"))[0], list(fh_data.values())
            )
        return structured_imgs

    def track(self) -> dict:
        all_grid_squares = set(self.epu_images.keys())
        if self.starfile:
            mics = self.extract(self.basepath / self.starfile)
            used_grid_squares = {m.grid_square for m in mics}
        else:
            used_grid_squares = all_grid_squares

        gui_directories = ["squares_all", "squares_used", "squares_not_used"]
        grid_square_names = {
            "squares_all": all_grid_squares,
            "squares_used": used_grid_squares,
            "squares_not_used": all_grid_squares - used_grid_squares,
        }
        with self.settings.open("a") as sf:
            sf.write(f"Total: {len(all_grid_squares)}\n")
            sf.write(f"Used: {len(used_grid_squares)}\n")
            sf.write(f"Not: {len(all_grid_squares - used_grid_squares)}\n")

        output = {
            "squares_all": {
                k: v
                for k, v in self.epu_images.items()
                if k in grid_square_names["squares_all"]
            },
            "squares_used": {
                k: v
                for k, v in self.epu_images.items()
                if k in grid_square_names["squares_used"]
            },
            "squares_not_used": {
                k: v
                for k, v in self.epu_images.items()
                if k in grid_square_names["squares_not_used"]
            },
        }
        return output
