import functools
import pathlib
import os
from gemmi import cif
from typing import Dict, List, NamedTuple


class Micrograph(NamedTuple):
    name: pathlib.Path
    grid_square: str
    foil_hole: str


class EPUTracker:
    def __init__(
        self,
        basepath: pathlib.Path,
        epudir: pathlib.Path,
        suffix: str,
        starfile: pathlib.Path,
        column: str,
    ):
        self.basepath = basepath
        self.epudir = epudir
        self.suffix = suffix
        self.starfile = starfile
        self.column = column
        self.outdir = self.basepath / "EPU_analysis"
        if self.outdir.is_dir():
            print(f"Directory EOU_analysis already found in {self.basepath}; removing")

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
            sf.write("Tracking settings")
            sf.write(f"Star: {self.basepath / self.starfile}")
            sf.write(f"EPU: {self.epudir}")
            sf.write(f"Column: {self.column}")
            sf.write(f"Suffix: {self.suffix}")
        (self.outdir / "star").mkdir()

    @staticmethod
    def _get_gs(mic: pathlib.Path) -> str:
        for p in mic.parts:
            if "GridSquare" in p:
                return p.split("_")[-1]

    @staticmethod
    def _get_fh(mic: pathlib.Path) -> str:
        split_name = mic.name.split("_")
        i = split_name.index("FoilHole")
        return split_name[i + 1]

    def extract(self, starfile: pathlib.Path) -> List[Micrograph]:
        gemmi_readable = os.fspath(starfile)
        star_doc = cif.read_file(gemmi_readable)
        column_data: List[pathlib.Path] = []
        for block in star_doc:
            col = list(block.find_loop(self.column))
            if col:
                column_data = [pathlib.Path(c) for c in col]
                break
        print(f"Number of particles: {len(column_data)}")
        unique_mics = {
            Micrograph(mic, self._get_gs(mic), self._get_fh(mic))
            for mic in column_data
            if mic.endswith(self.suffix)
        }
        print(f"Number of micrographs: {len(unique_mics)}")
        return unique_mics

    @property
    @functools.lru_cache(maxsize=1)
    def epu_images(self) -> Dict[str, Dict[str, List[pathlib.Path]]]:
        ims = self.epudir.glob("**/*.jpg")
        structured_ims = {}
        for im in ims:
            gs = self._get_gs(im)
            fh = self._get_fh(im)
            if structured_ims.get(gs):
                try:
                    structured_ims[gs][fh].append(im)
                except KeyError:
                    structured_ims[gs][fh] = [im]
            else:
                structured_ims[gs] = {fh: [im]}
        return structured_ims

    def track(self):
        mics = self.extract(self.basepath / self.starfile)
        used_grid_squares = {m.grid_sqaure for m in mics}
        
