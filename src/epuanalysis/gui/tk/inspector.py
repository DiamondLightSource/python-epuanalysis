import os
import tkinter as tk
from pathlib import Path
from PIL import Image, ImageTk
from functools import partial
from epuanalysis.scale import ImageScale
from epuanalysis.gui import _BaseFrame
from epuanalysis.gui.tk import draw_scale, selection_box, _GridEntry, tk_image
from epuanalysis.gui.tk.distributions import DistributionLoader
from typing import Dict, NamedTuple, Optional, Tuple


class InspectorFrame(_BaseFrame):
    def __init__(
        self,
        title: str,
        geometry: str = "1420x1420",
        data: Optional[dict] = None,
        detector_dimensions: Tuple[int, int] = (2048, 2048),
    ):
        super().__init__(title)
        self.frame = tk.Toplevel()
        self.frame.title(self.title)
        self.frame.geometry(geometry)
        self._detector_dims = detector_dimensions
        self.data = data or {}
        first_grid_square = next(iter(self.data.values()))
        self._square = first_grid_square
        first_foil_hole = first_grid_square.foil_holes[0]
        self._foilhole = first_foil_hole
        self._micrograph = first_foil_hole.exposures[0][0]
        self._grid: Dict[str, _GridEntry] = {
            "squares": _GridEntry((0, 0), (10, 45)),
            "foilholes": _GridEntry((0, 2), (10, 45)),
            "micrographs": _GridEntry((0, 4), (10, 45)),
            "img_square": _GridEntry((0, 395), (400, 400)),
            "img_foil_hole": _GridEntry((432, 395), (400, 400)),
            "img_micrograph": _GridEntry((862, 395), (400, 400)),
        }

        self.vars["entry_square"] = tk.Entry(self.frame, width=45, state="normal")
        self.vars["entry_square"].grid(column=2, row=11, sticky=tk.W)

        self.vars["entry_foilhole"] = tk.Entry(self.frame, width=45, state="normal")
        self.vars["entry_foilhole"].grid(column=4, row=11, sticky=tk.W)

        self.vars["entry_micrograph"] = tk.Entry(self.frame, width=45, state="normal")
        self.vars["entry_micrograph"].grid(column=6, row=11, sticky=tk.W)

        self._image_scale: Dict[str, ImageScale] = {
            "square": ImageScale(
                self._square.grid_square_img,
                name="img_square",
                detector_dimensions=self._detector_dims,
            ),
        }
        self._image_scale["foilhole"] = ImageScale(
            self._foilhole.foil_hole_img,
            name="img_foil_hole",
            detector_dimensions=self._detector_dims,
            above={self._square.name: self._image_scale["square"]},
            flip=(True, True),
        )
        self._image_scale["micrograph"] = ImageScale(
            self._micrograph,
            name="img_micrograph",
            detector_dimensions=self._detector_dims,
            above={self._foilhole.foil_hole_img: self._image_scale["foilhole"]},
        )

        self.vars["img_square"] = tk_image(
            self.frame, self._image_scale["square"], self._grid
        )
        self.vars["img_foil_hole"] = tk_image(
            self.frame, self._image_scale["foilhole"], self._grid
        )
        self.vars["img_micrograph"] = tk_image(
            self.frame, self._image_scale["micrograph"], self._grid
        )

        self.vars["squares"] = selection_box(
            self.frame,
            self._grid["squares"].position,
            self._grid["squares"].size,
            self._select_square,
        )
        self.vars["foilholes"] = selection_box(
            self.frame,
            self._grid["foilholes"].position,
            self._grid["foilholes"].size,
            self._select_foilhole,
        )
        self.vars["micrographs"] = selection_box(
            self.frame,
            self._grid["micrographs"].position,
            self._grid["micrographs"].size,
            self._select_micrograph,
        )

        self._refresh_list("squares", [d.name for d in self.data.values()])
        self._refresh_list("foilholes", [fh.name for fh in self._square.foil_holes])
        self._refresh_list("micrographs", [p[0] for p in self._foilhole.exposures])

    def _select_square(self, evt):
        try:
            self._square = self.data[
                self.vars["squares"].get(self.vars["squares"].curselection())
            ]
            self._image_scale["square"] = ImageScale(
                self._square.grid_square_img,
                name="img_square",
                detector_dimensions=self._detector_dims,
            )
        except tk.TclError:
            return
        self.draw_scale(
            self._image_scale["square"], "img_square", entry="entry_square", reset_entry="foilholes"
        )
        self._refresh_list("foilholes", [fh.name for fh in self._square.foil_holes])

    def _select_foilhole(self, evt):
        try:
            self._foilhole = [
                fh
                for fh in self._square.foil_holes
                if fh.name
                == self.vars["foilholes"].get(self.vars["foilholes"].curselection())
            ][0]
            self._image_scale["foilhole"] = ImageScale(
                self._foilhole.foil_hole_img,
                name="img_foil_hole",
                detector_dimensions=self._detector_dims,
                above={self._square.name: self._image_scale["square"]},
                flip=(True, True),
            )
        except tk.TclError:
            return
        self.draw_scale(
            self._image_scale["foilhole"],
            "img_foil_hole",
            entry="entry_foilhole",
            reset_entry="micrographs",
        )
        self._refresh_list("micrographs", [p[0] for p in self._foilhole.exposures])

    def _select_micrograph(self, evt):
        try:
            self._micrograph = [
                p[0]
                for p in self._foilhole.exposures
                if str(p[0])
                == self.vars["micrographs"].get(self.vars["micrographs"].curselection())
            ][0]
            self._image_scale["micrograph"] = ImageScale(
                self._micrograph,
                name="img_micrograph",
                detector_dimensions=self._detector_dims,
                above={self._foilhole.foil_hole_img: self._image_scale["foilhole"]},
            )
        except tk.TclError:
            return
        self.draw_scale(self._image_scale["micrograph"], "img_micrograph", entry="entry_micrograph")

    def _refresh_list(self, key: str, items: list):
        for i in items:
            self.vars[key].insert(tk.END, i)

    def draw_scale(
        self,
        imscale: ImageScale,
        varname: str,
        entry: str = "",
        reset_entry: str = "",
        img_override: Optional[Image.Image] = None,
    ):
        load = img_override or imscale.pil_image
        width, height = load.size
        ratio = width / height
        load = load.resize(
            (self._grid[varname].size[0], int(self._grid[varname].size[0] / ratio)),
            Image.ANTIALIAS,
        )
        render = ImageTk.PhotoImage(load)
        self.vars[varname] = tk.Label(self.frame, image=render)
        self.vars[varname].image = render
        self.vars[varname].place(
            x=self._grid[varname].position[0], y=self._grid[varname].position[1]
        )

        if reset_entry:
            self.vars[reset_entry].delete(0, tk.END)
        if entry:
            name = os.path.basename(imscale.image)
            self.vars[entry].delete(0, tk.END)
            self.vars[entry].insert(0, name)
        for k, abv in imscale.above.items():
            if not abv._frame:
                curr_scale = imscale
                iov = curr_scale.mark_image(
                    (curr_scale.cx, curr_scale.cy), scale_shift=1, target_tag=k
                )
                self.draw_scale(abv, abv.name, img_override=iov)
            else:
                curr_scale = imscale
                iov = curr_scale.mark_image(
                    (curr_scale.cx, curr_scale.cy), scale_shift=1, target_tag=k
                )
                abv._frame.draw_scale(abv, abv.name, img_override=iov)
