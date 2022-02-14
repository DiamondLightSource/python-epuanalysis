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

import os
import platform
import subprocess
import tkinter as tk
from pathlib import Path
from tkinter import *
from tkinter import filedialog
from tkinter.ttk import Progressbar

from epuanalysis.tracking import EPUTracker
from epuanalysis.epu_star_to_epu_browser_inspect import open_inspection_gui
from epuanalysis.frame import GUIFrame

###############################################################################


class Browser(GUIFrame):
    def __init__(self, title: str, geometry: str = "650x300"):
        super().__init__(title, geometry=geometry)
        self._bar: Progressbar = Progressbar(
            self.frame, length=200, style="black.Horizontal.TProgressbar"
        )
        self._bar["value"] = 0
        self._generate_items()
        self._image_structure: dict = {}
        self.frame.mainloop()

    def _generate_items(self):
        epu_var = tk.StringVar()
        self._entries["epu"] = self._make_button(
            self.row(), "Browse epu", self._browse_epu, var=epu_var
        )

        star_var = tk.StringVar()
        self._entries["star"] = self._make_button(
            self.row(), "Browse star", self._browse_star, var=star_var
        )

        column_var = tk.StringVar()
        self._entries["column"] = self._make_label(
            self.row(), "Star column:", var=column_var
        )

        suffix_var = tk.StringVar()
        self._entries["suffix"] = self._make_label(
            self.row(), "Data suffix:", var=suffix_var
        )

        self._bar.grid(column=1, row=self.row())

        row = self.row()
        button_run = tk.Button(self.frame, text="Run", command=self.run)
        button_run.grid(column=2, row=row)
        button_clear = tk.Button(self.frame, text="Clear", command=self.clear_all)
        button_clear.grid(column=3, row=row)

        analysis_lbl = Label(self.frame, text="Analysis:")
        analysis_lbl.grid(column=0, row=self.row())

        ## Information and analysis
        row = self.row()
        total_lbl = Label(self.frame, text="Total squares:")
        total_lbl.grid(column=0, row=row)
        self._entries["total"] = self._make_button(
            row, "View all", self._open_total, columns=(1, 2)
        )

        row = self.row()
        used_lbl = Label(self.frame, text="Used:")
        used_lbl.grid(column=0, row=row)
        self._entries["used"] = self._make_button(
            row, "View used", self._open_used, columns=(1, 2)
        )

        row = self.row()
        not_used_lbl = Label(self.frame, text="Not used:")
        not_used_lbl.grid(column=0, row=row)
        self._entries["unused"] = self._make_button(
            row, "View not used", self._open_not_used, columns=(1, 2)
        )

        inspect_button = tk.Button(
            self.frame, text="Inspect EPU images", command=self.inspect
        )
        inspect_button.grid(column=2, row=self.row())
        self._pop_path_fields()
        self._pop_analysis_fields()

    def _browse_epu(self):
        # Browse to dir
        self.frame.filename = filedialog.askdirectory(
            initialdir="~", title="Select directory"
        )
        epuin = self.frame.filename
        # delete content from position 0 to end
        self._entries["epu"].delete(0, tk.END)
        # insert new_text at position 0
        self._entries["epu"].insert(0, epuin)

    def _browse_star(self):
        # Browse to file
        self.frame.filename = filedialog.askopenfilename(
            initialdir="~",
            title="Select file",
            filetypes=(("all files", "*.*"), ("star files", "*.star")),
        )
        starin = self.frame.filename
        # delete content from position 0 to end
        self._entries["star"].delete(0, tk.END)
        # insert new_text at position 0
        self._entries["star"].insert(0, starin)

    def clear_all(self):
        self._clear_analysis()
        self._clear_paths()

    def _clear_paths(self):
        self._entries["star"].delete(0, tk.END)
        self._entries["epu"].delete(0, tk.END)
        self._entries["column"].delete(0, tk.END)
        self._entries["suffix"].delete(0, tk.END)

    def _clear_analysis(self):
        self._entries["total"].delete(0, tk.END)
        self._entries["used"].delete(0, tk.END)
        self._entries["unused"].delete(0, tk.END)

    def run(self):
        # Get entries
        star = self._entries["star"].get()
        epu = self._entries["epu"].get()
        column = self._entries["column"].get()
        suffix = self._entries["suffix"].get()
        # If entries empty then fill with none
        if not epu:
            self._entries["epu"].insert(0, "None")
        if not star:
            self._entries["star"].insert(0, "None")
            star = None
        if not column:
            self._entries["column"].insert(0, "None")
            column = None
        if not suffix:
            self._entries["suffix"].insert(0, "None")
            suffix = None
        if star is None:
            starpath = None
        else:
            starpath = Path(star)
        tracker = EPUTracker(
            Path("."),
            Path(epu),
            suffix=suffix,
            starfile=starpath,
            column=column,
        )
        self._image_structure = tracker.track()
        self._pop_analysis_fields()

    def _pop_analysis_fields(self):
        ## Get data if analysis already performed
        try:
            with open("./EPU_analysis/settings.dat") as f:
                print("Populating fields with previous analysis")
                self._clear_analysis()
                for line in f:
                    print(line)
                    if "Total:" in line:
                        total = line.strip().split()
                    if "Used:" in line:
                        used = line.strip().split()
                    if "Not:" in line:
                        notused = line.strip().split()
        ## Populate fields with defaults if analysis not performed
        except IOError:
            print("Previous analysis not found")
            total = "T0"
            used = "U0"
            notused = "N0"
        # Fill varibales if no value found
        try:
            total
        except NameError:
            total = "00"
        try:
            used
        except NameError:
            used = "00"
        try:
            notused
        except NameError:
            notused = "00"
        # Fill fields if analysis already performed
        try:
            self._entries["total"].insert(0, total[1])
            self._entries["used"].insert(0, used[1])
            self._entries["unused"].insert(0, notused[1])
        except IndexError:
            print("Data not present, although previous analysis performed...")

    def _pop_path_fields(self):
        ## Populate fields if analysis already performed
        try:
            with open("./EPU_analysis/settings.dat") as f:
                print("Populating fields with previous paths")
                self._clear_paths()
                for line in f:
                    if "Star" in line:
                        star = line.strip().split()
                    if "EPU" in line:
                        epu = line.strip().split()
                    if "Column" in line:
                        column = line.strip().split()
                    if "Suffix" in line:
                        suffix = line.strip().split()
            self._entries["star"].insert(0, star[1])
            self._entries["epu"].insert(0, epu[1])
            self._entries["column"].insert(0, column[1])
            self._entries["suffix"].insert(0, suffix[1])
        except IOError:
            print("Previous analysis not found")

    @staticmethod
    def open_file(path):
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])

    def _open_total(self):
        # Browse to dir
        pass

    def _open_used(self):
        # Browse to dir
        pass

    def _open_not_used(self):
        # Browse to dir
        pass

    def inspect(self):
        # Browse to dir
        open_inspection_gui(self._image_structure)


def run():
    Browser("EPU analysis from Relion star file")
