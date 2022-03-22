#!/usr/bin/env python
#

############################################################################
#
# Author: "Kyle L. Morris"
# eBIC Diamond Light Source 2022
# MRC London Institute of Medical Sciences 2019
#
# This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
############################################################################

# TO DO:
# 1) Remove dependancy on global variables
# 2) Only display jpg in listboxes that have associated _FoilHoles.dat

import os
import tkinter as tk

from PIL import ImageTk, Image
from pathlib import Path

import epuanalysis

from epuanalysis.epu_xml_inspector import inspect_xml
from epuanalysis.plot_coords import plot_coords
from epuanalysis.frame import GUIFrame
from epuanalysis.tracking import FoilHole
from epuanalysis.scale import ImageScale

from typing import Callable, List, Optional, Tuple


def RGBAImage(path):
    return Image.open(path).convert("RGBA")


class Inspector(GUIFrame):
    def __init__(self, title: str, image_structure: dict, geometry: str = "1420x820"):
        super().__init__(title, geometry=geometry, top_level=True)
        self._image_structure = image_structure
        self._current_grid_square: str = ""
        self._current_foil_hole: Optional[FoilHole] = None
        self._current_foil_hole_scale: Optional[ImageScale] = None
        self._foil_holes_list = []
        self.pick_state = tk.IntVar()
        self.pick_state.set(0)
        self._star: List[str] = []
        self._epu: List[str] = []
        self._suffix: List[str] = []
        self._load_settings()
        self._generate_items()
        self.frame.mainloop()

    def _load_settings(self):
        try:
            with open("EPU_analysis/settings.dat") as f:
                for line in f:
                    if "Star" in line:
                        self._star = line.strip().split()
                    if "EPU" in line:
                        self._epu = line.strip().split()
                    if "Suffix" in line:
                        self._suffix = line.strip().split()
        ## Populate fields with defaults if analysis not performed
        except IOError:
            print("Previous analysis not found")

    def _generate_items(self):
        row = self.row()
        lbl = tk.Label(
            self.frame,
            text="Show all Squares or only Squares found in star file:",
            anchor=tk.W,
            justify=tk.LEFT,
        )
        lbl.grid(column=2, row=row)
        lbl = tk.Label(
            self.frame,
            text="Show all FoilHoles or only FoilHoles with particles:",
            anchor=tk.W,
            justify=tk.LEFT,
        )
        lbl.grid(column=4, row=row)

        row = self.row()
        self._entries["rad_square_selection"] = self._make_radio_button(
            row, 2, "squares_all", "All", self._radio_click_sq, sticky="w"
        )
        self._make_radio_button(
            row,
            2,
            "squares_used",
            "Used",
            self._radio_click_sq,
            variable=self._entries["rad_square_selection"],
        )
        self._make_radio_button(
            row,
            2,
            "squares_not_used",
            "Not used",
            self._radio_click_sq,
            variable=self._entries["rad_square_selection"],
            sticky="e",
        )

        self._entries["rad_foil_selection"] = self._make_radio_button(
            row, 4, "foilAll", "All", self._radio_click_foil, sticky="w"
        )
        self._make_radio_button(
            row,
            4,
            "foilUsed",
            "Used",
            self._radio_click_foil,
            variable=self._entries["rad_foil_selection"],
        )
        self._make_radio_button(
            row,
            4,
            "foilNot",
            "Not used",
            self._radio_click_foil,
            variable=self._entries["rad_foil_selection"],
            sticky="e",
        )

        lbl = tk.Label(self.frame, text="                                           ")
        lbl.grid(sticky="w", column=4, row=self.row())

        self._entries["pick_check"] = tk.Checkbutton(
            self.frame, text="Particles", var=self.pick_state
        )
        self._entries["pick_check"].grid(sticky="e", column=10, row=11)

        mic_x_var = tk.StringVar()
        self._entries["mic_x"] = self._make_label(
            12,
            "x (px):",
            column_entry=10,
            column_label=9,
            width=3,
            var=mic_x_var,
            sticky="e",
        )
        self._entries["mic_x"].insert(0, "4096")

        mic_y_var = tk.StringVar()
        self._entries["mic_y"] = self._make_label(
            13,
            "y (px):",
            column_entry=10,
            column_label=9,
            width=3,
            var=mic_y_var,
            sticky="e",
        )
        self._entries["mic_y"].insert(0, "4096")

        mic_d_var = tk.StringVar()
        self._entries["mic_d"] = self._make_label(
            14,
            "D (px):",
            column_entry=10,
            column_label=9,
            width=3,
            var=mic_d_var,
            sticky="e",
        )
        self._entries["mic_d"].insert(0, "150")

        values = ["K2", "K3", "FII", "FIII", "Other"]
        self._entries["combo"] = tk.ttk.Combobox(self.frame, values=values, width=10)
        self._entries["combo"].current(4)
        self._entries["combo"].grid(column=10, row=15)
        self._entries["combo"].bind("<<ComboboxSelected>>", self._select_detector)

        self._entries["xml_button"] = tk.Button(
            self.frame, text="Inspect xml", command=self._inspect_xml
        )
        self._entries["xml_button"].grid(column=10, row=16)

        row = self.row()

        lbl = tk.Label(self.frame, text="Squares:")
        lbl.grid(column=2, row=row)
        lbl = tk.Label(self.frame, text="Foil Holes:")
        lbl.grid(column=4, row=row)
        lbl = tk.Label(self.frame, text="Holes:")
        lbl.grid(column=6, row=row)

        row = self.row()

        self._entries["square_list"] = self._make_scrollbar(row, 0, self._square_select)
        self._entries["foil_list"] = self._make_scrollbar(row, 2, self._foil_select)
        self._entries["mic_list"] = self._make_scrollbar(row, 4, self._mic_select)

        self._pop_squares()

        lbl = tk.Label(
            self.frame, text="Current square selection:", anchor=tk.W, justify=tk.LEFT
        )
        lbl.grid(sticky="w", column=2, row=10)
        self._entries["entry_square"] = tk.Entry(self.frame, width=45, state="normal")
        self._entries["entry_square"].grid(column=2, row=11, sticky=tk.W)

        lbl = tk.Label(
            self.frame, text="Current foil selection:", anchor=tk.W, justify=tk.LEFT
        )
        lbl.grid(sticky="w", column=4, row=10)
        self._entries["entry_foil"] = tk.Entry(self.frame, width=45, state="normal")
        self._entries["entry_foil"].grid(column=4, row=11, sticky=tk.W)

        lbl = tk.Label(
            self.frame,
            text="Current micrograph selection:",
            anchor=tk.W,
            justify=tk.LEFT,
        )
        lbl.grid(sticky="w", column=6, row=10)
        self._entries["entry_mic"] = tk.Entry(self.frame, width=45, state="normal")
        self._entries["entry_mic"].grid(column=6, row=11, sticky=tk.W)

    def _make_scrollbar(self, row: int, column: int, command: Callable) -> tk.Listbox:
        scrollbar = tk.Scrollbar(self.frame)
        scrollbar.grid(row=row, column=column + 3, rowspan=5, sticky=tk.N + tk.S)
        lb = tk.Listbox(self.frame, height=10, width=45, yscrollcommand=scrollbar.set)
        lb.grid(row=row, column=column + 2, rowspan=5, sticky=tk.E + tk.W)
        lb.bind("<<ListboxSelect>>", command)
        scrollbar.config(command=lb.yview)
        return lb

    def _make_radio_button(
        self,
        row: int,
        column: int,
        value: str,
        text: str,
        command: Callable,
        variable: Optional[tk.StringVar] = None,
        sticky: str = "",
    ):
        radio_var = tk.StringVar()
        rad = tk.Radiobutton(
            self.frame,
            text=text,
            indicatoron=0,
            value=value,
            command=command,
            variable=variable or radio_var,
        )
        rad.grid(sticky=sticky, column=column, row=row)
        return variable or radio_var

    def _radio_click_sq(self):
        value = self._entries["rad_square_selection"].get()
        self._entries["square_list"].delete(0, tk.END)
        for gs in self._image_structure[value].values():
            self._entries["square_list"].insert(tk.END, gs.name)
        wc = len(self._image_structure[value])
        lbl = tk.Label(self.frame, text="Number of Squares: " + str(wc) + "  ")
        lbl.grid(sticky="w", column=2, row=12)

        lbl = tk.Label(self.frame, text="Number of FoilHoles:       ")
        lbl.grid(sticky="w", column=4, row=12)

        lbl = tk.Label(self.frame, text="Number of Micrographs:     ")
        lbl.grid(sticky="w", column=6, row=12)

    def _radio_click_foil(self):
        pass

    def _select_detector(self, event):
        detector = self._entries["combo"].get()
        self._entries["mic_x"].delete(0, tk.END)
        self._entries["mic_y"].delete(0, tk.END)
        if detector == "K2":
            self._entries["mic_x"].insert(0, "3710")
            self._entries["mic_y"].insert(0, "3838")
        elif detector == "K3":
            self._entries["mic_x"].insert(0, "5760")
            self._entries["mic_y"].insert(0, "4092")
        elif detector == "FII":
            self._entries["mic_x"].insert(0, "4096")
            self._entries["mic_y"].insert(0, "4096")
        elif detector == "FIII":
            self._entries["mic_x"].insert(0, "4096")
            self._entries["mic_y"].insert(0, "4096")
        elif detector == "Other":
            self._entries["mic_x"].insert(0, "")
            self._entries["mic_y"].insert(0, "")

    def _inspect_xml(self):
        # Write the current micrograph to a file for reading by xml inspection gui
        # This is not the right way, pass over as variable properly
        # https://www.code4example.com/python/tkinter/tkinter-passing-variables-between-windows/
        value = self._entries["mic_list"].get(self._entries["mic_list"].curselection())
        imgpath = value.rstrip()
        with open(".micrograph.dat", "w") as f:
            f.write(imgpath + "\n")
        # Open the xml inspection GUI
        inspect_xml()

    def _pop_squares(self):
        # Clear current square list
        self._entries["square_list"].delete(0, tk.END)
        ## Populate square list box
        wc = len(self._image_structure["squares_all"])
        lbl = tk.Label(self.frame, text="Number of Squares: " + str(wc) + "  ")
        lbl.grid(sticky="w", column=2, row=12)

        lbl = tk.Label(self.frame, text="Number of FoilHoles:        ")
        lbl.grid(sticky="w", column=4, row=12)

        lbl = tk.Label(self.frame, text="Number of Micrographs:      ")
        lbl.grid(sticky="w", column=6, row=12)

    def _select(
        self,
        img_path: str,
        img_name: str,
        position: Tuple[int, int],
        next_level: str = "",
        entry: str = "",
        img: Optional[Image.Image] = None,
    ) -> str:
        if img:
            width, height = img.size
            ratio = width / height
            load = img.resize((400, int(400 / ratio)), Image.ANTIALIAS)
        else:
            load = RGBAImage(img_path)
            width, height = load.size
            ratio = width / height
            load = load.resize((400, int(400 / ratio)), Image.ANTIALIAS)
        render = ImageTk.PhotoImage(load)
        self._entries[img_name] = tk.Label(self.frame, image=render)
        self._entries[img_name].image = render
        self._entries[img_name].place(x=position[0], y=position[1])
        if next_level:
            self._entries[next_level].delete(0, tk.END)
        if entry:
            name = os.path.basename(img_path)
            self._entries[entry].delete(0, tk.END)
            self._entries[entry].insert(0, name)

    def _square_select(self, evt):
        try:
            value = self._entries["square_list"].get(
                self._entries["square_list"].curselection()
            )
        except tk.TclError:
            return
        imgpath = self._image_structure[self._entries["rad_square_selection"].get()][
            value
        ].grid_square_img
        self._current_grid_square = value
        self._current_grid_square_scale = ImageScale(
            Path(imgpath), name="img_square", detector_dimensions=(2048, 2048)
        )
        self.add_scale(self._current_grid_square_scale, (0, 395))
        self.draw_scale(self._current_grid_square_scale.name, entry="entry_square", reset_entry="foil_list")

        ## Populate list box
        self._foil_holes_list = self._image_structure[
            self._entries["rad_square_selection"].get()
        ][value].foil_holes
        for item in [fh.name for fh in self._foil_holes_list]:
            ## Populate FoilHole list based on level of particle filtering selected
            self._entries["foil_list"].insert(tk.END, item)

        ## Print useful information in label
        lbl = tk.Label(
            self.frame,
            text="Number of FoilHoles: "
            + str(self._entries["foil_list"].size())
            + "    ",
        )
        lbl.grid(sticky="w", column=4, row=12)
        self.clear_pick_no()

    def _foil_select(self, evt):
        try:
            value = self._entries["foil_list"].get(
                self._entries["foil_list"].curselection()
            )
        except tk.TclError:
            return
        foil_holes = [
            fh
            for fh in self._image_structure[
                self._entries["rad_square_selection"].get()
            ][self._current_grid_square].foil_holes
            if fh.name == value
        ]
        foil_hole = foil_holes[0]
        self._current_foil_hole = foil_hole
        self._current_foil_hole_scale = ImageScale(
            foil_hole.foil_hole_img,
            name="img_foil",
            above={
                self._current_grid_square_scale.image: self._current_grid_square_scale
            },
            detector_dimensions=(2048, 2048),
        )
        self.add_scale(self._current_foil_hole_scale, (432, 395))
        self.draw_scale(self._current_foil_hole_scale.name, entry="entry_foil", reset_entry="mic_list")

        # Populate listbox
        for item in foil_hole.exposures:
            self._entries["mic_list"].insert(tk.END, item[0])
        ## Print useful information in label
        # Number of FoilHoles images
        lbl = tk.Label(
            self.frame, text=f"Number of Micrographs: {len(foil_hole.exposures)}"
        )
        lbl.grid(sticky="w", column=6, row=12)
        self.clear_pick_no()

    def _mic_select(self, evt):
        try:
            imgpath = self._entries["mic_list"].get(
                self._entries["mic_list"].curselection()
            )
        except tk.TclError:
            return
        # self._select(imgpath, "img_mic", (862, 395), entry="entry_mic")
        mic_scale = ImageScale(
            Path(imgpath),
            name="img_mic",
            above={self._current_foil_hole_scale.image: self._current_foil_hole_scale},
            detector_dimensions=(2048, 2048),
        )

        self.add_scale(mic_scale, (862, 395))
        self.draw_scale(mic_scale.name, entry="entry_mic")

       
        # Populate listbox
        for item in self._current_foil_hole.exposures:
            self._entries["mic_list"].insert(tk.END, item[0])

        for item in [fh.name for fh in self._foil_holes_list]:
            ## Populate FoilHole list based on level of particle filtering selected
            self._entries["foil_list"].insert(tk.END, item)

        # Report number of picked particles to GUI
        self.clear_pick_no()
        num_particles = None
        if self._current_foil_hole:
            for mic, num_parts in self._current_foil_hole.exposures:
                if str(mic) == imgpath:
                    num_particles = num_parts
                    break
        lbl = tk.Label(self.frame, text=f"No. of particles: {num_particles}")
        lbl.grid(sticky="W", column=10, row=11)
        if self.pick_state.get():
            self._plot_picks(imgpath)

    def _plot_picks(self, mic_path: str):
        plot_coords(
            Path(self._star[1]),
            Path(mic_path),
            int(self._entries["mic_x"].get()),
            int(self._entries["mic_y"].get()),
            float(self._entries["mic_d"].get()),
            Path("./EPU_analysis/star/"),
            flip=(False, True),
        )
        ##Load Micrograph image
        mic_load = RGBAImage(mic_path)
        mic_load = mic_load.resize((400, 400), Image.ANTIALIAS)
        ## Particle pick overlay
        par_load = RGBAImage("./EPU_analysis/star/particles.png")
        par_load = par_load.resize((400, 400), Image.ANTIALIAS)
        mic_load.paste(par_load, (0, 0), par_load)
        par_render = ImageTk.PhotoImage(mic_load)
        img_mic = tk.Label(self.frame, image=par_render)
        img_mic.image = par_render
        img_mic.place(x=862, y=395)

    def clear_pick_no(self):
        # Clear part picks report
        lbl = tk.Label(self.frame, text="         ")
        lbl.grid(sticky="W", column=8, row=11)


def open_inspection_gui(image_structure):
    inspector = Inspector(
        "EPU analysis from Relion star file", image_structure=image_structure
    )
