import functools
import os
import pathlib
from typing import Dict, List, NamedTuple, Set, Optional

from gemmi import cif


class Micrograph(NamedTuple):
    name: pathlib.Path
    grid_square: str
    foil_hole: str


class FoilHole(NamedTuple):
    name: str
    foil_hole_img: pathlib.Path
    exposures: List[pathlib.Path]


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
    ):
        self.basepath = basepath
        self.epudir = epudir
        self.suffix = suffix
        self.starfile = starfile
        self.column = column
        self.outdir = self.basepath / "EPU_analysis"
        if self.outdir.is_dir():
            print(f"Directory EPU_analysis already found in {self.basepath}; removing")

            def _remove_nonempty(dir_for_rm: pathlib.Path):
                for element in dir_for_rm.glob("*"):
                    if element.is_dir():
                        _remove_nonempty(element)
                    else:
                        element.unlink()
                dir_for_rm.rmdir()

            _remove_nonempty(self.outdir)
        self.outdir.mkdir()
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
        (self.outdir / "star").mkdir()

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
        for block in star_doc:
            col = list(block.find_loop(self.column))
            if col:
                column_data = [pathlib.Path(c) for c in col]
                break
        print(f"Number of particles: {len(column_data)}")
        print("micrograph found:", column_data)
        unique_mics = {
            Micrograph(mic, self._get_gs(mic), self._get_fh(mic))
            for mic in column_data
            if str(mic).endswith(self.suffix)
        }
        print("unique micrographs:", unique_mics, self.suffix)
        print(f"Number of micrographs: {len(unique_mics)}")
        return unique_mics

    @property
    @functools.lru_cache(maxsize=1)
    def epu_images(self) -> Dict[str, GridSquare]:
        structured_imgs = {}
        gridsquare_dirs = [p for p in self.epudir.glob("GridSquare*")]
        print(gridsquare_dirs)
        for gsd in gridsquare_dirs:
            foilholes = [p for p in (gsd / "FoilHoles").glob("FoilHole*.jpg")]
            fh_data = {}
            for fh in foilholes:
                fh_name = "_".join(fh.stem.split("_")[:2])
                fh_data[fh_name] = FoilHole(
                    fh_name,
                    fh,
                    [p for p in (gsd / "Data").glob("*.jpg") if fh_name in p.name],
                )
            structured_imgs[gsd.stem] = GridSquare(
                gsd.stem, list(gsd.glob("*.jpg"))[0], list(fh_data.values())
            )
        return structured_imgs

    def track(self):
        all_grid_squares = set(self.epu_images.keys())
        if self.starfile:
            print("extracting from:", self.basepath / self.starfile)
            mics = self.extract(self.basepath / self.starfile)
            print("micrographs:", mics)
            used_grid_squares = {m.grid_square for m in mics}
        else:
            used_grid_squares = all_grid_squares
        gui_directories = ["squares_all", "squares_used", "squares_not_used"]
        grid_square_names = {
            "squares_all": all_grid_squares,
            "squares_used": used_grid_squares,
            "squares_not_used": all_grid_squares - used_grid_squares,
        }
        print(all_grid_squares)
        print(used_grid_squares)
        print(self.epu_images)
        for gd in gui_directories:
            (self.outdir / gd).mkdir()
            for gs in grid_square_names[gd]:
                print(gd, gs)
                from_file = self.epu_images[gs].grid_square_img
                (self.outdir / gd / from_file.name).symlink_to(from_file)
                (self.outdir / gd / (from_file.stem + ".xml")).symlink_to(
                    from_file.with_suffix(".xml")
                )
                (self.outdir / gd / f"{gs}_FoilHoles").mkdir()
                (self.outdir / gd / f"{gs}_Data").mkdir()
                for fh in self.epu_images[gs].foil_holes:
                    (
                        self.outdir / gd / f"{gs}_FoilHoles" / (fh.foil_hole_img.name)
                    ).symlink_to(fh.foil_hole_img)
                    for im in fh.exposures:
                        (self.outdir / gd / f"{gs}_Data" / im.name).symlink_to(im)
                        (
                            self.outdir / gd / f"{gs}_Data" / (im.stem + ".xml")
                        ).symlink_to(im.with_suffix(".xml"))
                    (
                        self.outdir
                        / gd
                        / f"{gs}_FoilHoles"
                        / (fh.foil_hole_img.stem + ".xml")
                    ).symlink_to(fh.foil_hole_img.with_suffix(".xml"))
