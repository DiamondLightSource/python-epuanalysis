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
from epuanalysis.epu_star_to_epu_browser_inspect import inspect


###############################################################################

def run():

    # Defines buttons
    def browsestar():
        # Browse to file
        main_frame.filename = filedialog.askopenfilename(
            initialdir="~",
            title="Select file",
            filetypes=(("all files", "*.*"), ("star files", "*.star")),
        )
        starin = main_frame.filename
        # delete content from position 0 to end
        entrystar.delete(0, tk.END)
        # insert new_text at position 0
        entrystar.insert(0, starin)


    def browseepu():
        # Browse to dir
        main_frame.filename = filedialog.askdirectory(
            initialdir="~", title="Select directory"
        )
        epuin = main_frame.filename
        # delete content from position 0 to end
        entryepu.delete(0, tk.END)
        # insert new_text at position 0
        entryepu.insert(0, epuin)


    def clear_all():
        clear_analysis()
        clear_paths()


    def clear_paths():
        # delete content from position 0 to end
        entrystar.delete(0, tk.END)
        entryepu.delete(0, tk.END)
        entrycolumn.delete(0, tk.END)
        entrysuffix.delete(0, tk.END)


    def clear_analysis():
        # delete content from position 0 to end
        entryTotal.delete(0, tk.END)
        entryUsed.delete(0, tk.END)
        entryNotUsed.delete(0, tk.END)


    def run():
        # Get entries
        star = entrystar.get()
        epu = entryepu.get()
        column = entrycolumn.get()
        suffix = entrysuffix.get()
        # If entries empty then fill with none
        if not epu:
            entryepu.insert(0, "None")
        if not star:
            entrystar.insert(0, "None")
            star = None
        if not column:
            entrycolumn.insert(0, "None")
            column = None
        if not suffix:
            entrysuffix.insert(0, "None")
            suffix = None
        if star is None:
            starpath = None 
        else:
            starpath = Path(star)
        tracker = EPUTracker(
            Path("."), Path(epu) / "ImageDisk-1", suffix=suffix, starfile=starpath, column=column
        )
        tracker.track()
        pop_analysis_fields()


    def pop_analysis_fields():
        ## Get data if analysis already performed
        try:
            with open("./EPU_analysis/settings.dat") as f:
                print("Populating fields with previous analysis")
                clear_analysis()
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
            entryTotal.insert(0, total[1])
            entryUsed.insert(0, used[1])
            entryNotUsed.insert(0, notused[1])
        except IndexError:
            print("Data not present, although previous analysis performed...")


    def pop_path_fields():
        ## Populate fields if analysis already performed
        try:
            with open("./EPU_analysis/settings.dat") as f:
                print("Populating fields with previous paths")
                clear_paths()
                for line in f:
                    if "Star" in line:
                        star = line.strip().split()
                    if "EPU" in line:
                        epu = line.strip().split()
                    if "Column" in line:
                        column = line.strip().split()
                    if "Suffix" in line:
                        suffix = line.strip().split()
            entrystar.insert(0, star[1])
            entryepu.insert(0, epu[1])
            entrycolumn.insert(0, column[1])
            entrysuffix.insert(0, suffix[1])
        except IOError:
            print("Previous analysis not found")
            # entrystar.insert(0, "[Enter star file]")
            # entryepu.insert(0, "[Enter epu dir]")
            # entrycolumn.insert(0, "[Enter Relion star file column name]")
            # entrysuffix.insert(0, "[Enter suffix added to mic name by particle extraction]")


    def open_file(path):
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])


    def open_total():
        # Browse to dir
        open_file("./EPU_analysis/squares_all")


    def open_used():
        # Browse to dir
        open_file("./EPU_analysis/squares_used")


    def open_not_used():
        # Browse to dir
        open_file("./EPU_analysis/squares_not_used")


    def inspect():
        # Browse to dir
        inspect()


    ###############################################################################

    ### Create GUI
    main_frame = tk.Tk()

    main_frame.title("EPU analysis from Relion star file")
    main_frame.geometry("650x300")

    row = 0
    ## Text and button entry
    row += 1
    entry_epu = tk.StringVar()
    entryepu = tk.Entry(main_frame, width=40, textvariable=entry_epu)
    entryepu.grid(column=1, row=row)
    buttonepu = tk.Button(main_frame, text="Browse epu", command=browseepu)
    buttonepu.grid(column=0, row=row)
    # entrystar.pack(side=tk.LEFT)
    row += 1
    entry_star = tk.StringVar()
    entrystar = tk.Entry(main_frame, width=40, textvariable=entry_star)
    entrystar.grid(column=1, row=row)
    buttonstar = tk.Button(main_frame, text="Browse star", command=browsestar)
    buttonstar.grid(column=0, row=row)
    row += 1
    entry_column = tk.StringVar()
    entrycolumn = tk.Entry(main_frame, width=40, textvariable=entry_column)
    entrycolumn.grid(column=1, row=row)
    lbl = Label(main_frame, text="Star column:")
    lbl.grid(column=0, row=row)
    row += 1
    entry_suffix = tk.StringVar()
    entrysuffix = tk.Entry(main_frame, width=40, textvariable=entry_suffix)
    entrysuffix.grid(column=1, row=row)
    lbl = Label(main_frame, text="Data suffix:")
    lbl.grid(column=0, row=row)
    row += 1
    ## Progress bar
    # style = ttk.Style()
    # style.theme_use('default')
    # style.configure("black.Horizontal.TProgressbar", background='black')
    bar = Progressbar(main_frame, length=200, style="black.Horizontal.TProgressbar")
    bar.grid(column=1, row=row)
    row += 1
    ## Buttons
    buttonRun = tk.Button(main_frame, text="Run", command=run)
    buttonRun.grid(column=2, row=row)
    buttonClear = tk.Button(main_frame, text="Clear", command=clear_all)
    buttonClear.grid(column=3, row=row)
    row += 1
    lbl = Label(main_frame, text="Analysis:")
    lbl.grid(column=0, row=row)
    row += 1

    ## Information and analysis
    lbl = Label(main_frame, text="Total squares:")
    lbl.grid(column=0, row=row)
    entryTotal = Entry(main_frame, width=10, state="normal")
    entryTotal.grid(column=1, row=row)
    buttonTotal = tk.Button(main_frame, text="View all", command=open_total)
    buttonTotal.grid(column=2, row=row)
    row += 1

    lbl = Label(main_frame, text="Used:")
    lbl.grid(column=0, row=row)
    entryUsed = Entry(main_frame, width=10, state="normal")
    entryUsed.grid(column=1, row=row)
    buttonUsed = tk.Button(main_frame, text="View used", command=open_used)
    buttonUsed.grid(column=2, row=row)
    row += 1

    lbl = Label(main_frame, text="Not used:")
    lbl.grid(column=0, row=row)
    entryNotUsed = Entry(main_frame, width=10, state="normal")
    entryNotUsed.grid(column=1, row=row)
    buttonNotUsed = tk.Button(main_frame, text="View not used", command=open_not_used)
    buttonNotUsed.grid(column=2, row=row)
    row += 1

    buttonInspect = tk.Button(main_frame, text="Inspect EPU images", command=inspect)
    buttonInspect.grid(column=2, row=row)

    pop_path_fields()
    pop_analysis_fields()

    ## Progress bar default to 0
    bar["value"] = 0

    main_frame.mainloop()
