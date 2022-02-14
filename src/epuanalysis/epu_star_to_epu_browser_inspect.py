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
import sys
from tkinter import *
from tkinter import ttk

from PIL import ImageTk, Image
from pathlib import Path

import epuanalysis

from epuanalysis.epu_xml_inspector import inspect_xml
from epuanalysis.epu_plot_foilhole import plot_foilhole
from epuanalysis.plot_coords import plot_coords
from epuanalysis.frame import GUIFrame

from typing import Optional

###############################################################################

current_grid_square = ""


class Inspector(GUIFrame):
    def __init__(self, title: str, geometry: str = "1420x820"):
        super().__init__(title, geometry=geometry, top_level=True)

    def _generate_items(self):
        row = self.row()
        lbl = Label(
            self.frame,
            text="Show all Squares or only Squares found in star file:",
            anchor=tk.W,
            justify=tk.LEFT,
        )
        lbl.grid(column=2, row=row)
        lbl = Label(
            self.frame,
            text="Show all FoilHoles or only FoilHoles with particles:",
            anchor=tk.W,
            justify=tk.LEFT,
        )
        lbl.grid(column=4, row=row)

        row = self.row()
        self._entries["rad_square_selection"] = self._make_radio_button(
            row, 2, "squares_all", "All"
        )
        self._make_radio_button(
            row,
            2,
            "squares_used",
            "Used",
            variable=self._entries["rad_square_selection"],
        )
        self._make_radio_button(
            row,
            2,
            "squares_not_used",
            "Not used",
            variable=self._entries["rad_square_selection"],
        )

        self._entries["rad_foil_selection"] = self._make_radio_button(
            row, 4, "foilAll", "All"
        )
        self._make_radio_button(
            row, 4, "foilUsed", "Used", variable=self._entries["rad_foil_selection"]
        )
        self._make_radio_button(
            row, 4, "foilNot", "Not used", variable=self._entries["rad_foil_selection"]
        )

    def _make_radio_button(
        self,
        row: int,
        column: int,
        value: str,
        text: str,
        variable: Optional[tk.StringVar] = None,
    ):
        radio_var = tk.StringVar()
        rad = Radiobutton(
            self.frame,
            text=text,
            indicatoron=0,
            value=value,
            command=self.radio_click_sq,
            variable=variable or radio_var,
        )
        rad.grid(sticky="w", column=column, row=row)
        return variable or radio_var


def inspect_squares(image_structure):
    def inspectXml():
        # Write the current micrograph to a file for reading by xml inspection gui
        # This is not the right way, pass over as variable properly
        # https://www.code4example.com/python/tkinter/tkinter-passing-variables-between-windows/
        value = miclist.get(miclist.curselection())
        imgpath = value.rstrip()
        print(imgpath)
        file = open(".micrograph.dat", "w")
        file.write(imgpath + "\n")
        file.close()
        # Open the xml inspection GUI
        inspect_xml()

    def file_len(fname):
        length = 0
        with open(fname, "r") as f:
            length = len(f.readlines())
        return length

    def popSquares():
        # Clear current square list
        sqlist.delete(0, tk.END)
        ## Populate square list box
        wc = len(image_structure["squares_all"])
        lbl = Label(main_frame, text="Number of Squares: " + str(wc) + "  ")
        lbl.grid(sticky="w", column=2, row=12)

        lbl = Label(main_frame, text="Number of FoilHoles:        ")
        lbl.grid(sticky="w", column=4, row=12)

        lbl = Label(main_frame, text="Number of Micrographs:      ")
        lbl.grid(sticky="w", column=6, row=12)

        # lbl = Label(main_frame, text='Greyscale of FoilHole Micrograph(s):      ')
        lbl = Label(main_frame, text="                                           ")
        lbl.grid(sticky="w", column=6, row=13)
        # lbl = Label(main_frame, text='Greyscale of selected Micrograph(s):      ')
        lbl = Label(main_frame, text="                                           ")
        lbl.grid(sticky="w", column=6, row=14)

        lbl = Label(main_frame, text="No. of particles:")
        lbl.grid(sticky="w", column=8, row=15)

    def popConditional():
        # Clear current list
        sqlist.delete(0, tk.END)
        # Get radio button variable to load All, Used, or NotUsed squares
        value = radioSq.get()
        ## Populate list box
        for gs in image_structure[value].values():
            sqlist.insert(tk.END, gs.name)
        wc = len(image_structure[value])
        lbl = Label(main_frame, text="Number of Squares: " + str(wc) + "  ")
        lbl.grid(sticky="w", column=2, row=12)

        lbl = Label(main_frame, text="Number of FoilHoles:       ")
        lbl.grid(sticky="w", column=4, row=12)

        lbl = Label(main_frame, text="Number of Micrographs:     ")
        lbl.grid(sticky="w", column=6, row=12)

        # lbl = Label(main_frame, text='Greyscale of FoilHole Micrograph(s):      ')
        lbl = Label(main_frame, text="                                           ")
        lbl.grid(sticky="w", column=6, row=13)
        # lbl = Label(main_frame, text='Greyscale of selected Micrograph(s):      ')
        lbl = Label(main_frame, text="                                           ")
        lbl.grid(sticky="w", column=6, row=14)

        lbl = Label(main_frame, text="No. of particles:")
        lbl.grid(sticky="w", column=8, row=15)

    def SquareSelect(evt):
        value = sqlist.get(sqlist.curselection())
        # value = sqlist.get(ACTIVE)
        # imgpath = value.rstrip()
        imgpath = image_structure[radioSq.get()][value].grid_square_img
        # Define global variable for use outside def, Square
        global squarepath
        squarepath = imgpath
        # Load square image
        load = RBGAImage(imgpath)
        width, height = load.size
        print(width, height)
        ratio = width / height
        print(ratio)
        load = load.resize((400, int(400 / ratio)), Image.ANTIALIAS)
        render = ImageTk.PhotoImage(load)
        imgSq = Label(main_frame, image=render)
        imgSq.image = render
        imgSq.place(x=0, y=395)

        # Report selected square to GUI
        name = os.path.basename(imgpath)
        entrySq.delete(0, tk.END)
        entrySq.insert(0, name)
        # Populate Foil Holes
        # value = os.path.splitext(imgpath)[0]

        ## Clear FoilHole list box
        foillist.delete(0, tk.END)
        ## Populate list box
        try:
            for item in [
                fh.name for fh in image_structure[radioSq.get()][value].foil_holes
            ]:
                ## Populate FoilHole list based on level of particle filtering selected
                foillist.insert(tk.END, item)

                ## Populate fields with defaults if analysis not performed
        except IOError:
            print(value + "_FoilHoles.dat not found")
        ## Print useful information in label
        # Number of FoilHoles images
        lbl = Label(
            main_frame, text="Number of FoilHoles: " + str(foillist.size()) + "    "
        )
        lbl.grid(sticky="w", column=4, row=12)
        clearPickNo()
        ## Select first FoilHole of selected Square
        # foillist.selection_set(first=0)
        # select(foillist, 0, FoilSelect)
        global current_grid_square
        current_grid_square = value

    def select(self, index, command):
        self.activate(index)
        self.select_clear(0, "end")
        self.selection_set(index)
        self.see(index)
        self.selection_anchor(index)
        command(None)

    def FoilSelect(evt):
        value = foillist.get(foillist.curselection())
        foil_holes = [
            fh
            for fh in image_structure[radioSq.get()][current_grid_square].foil_holes
            if fh.name == value
        ]
        foil_hole = foil_holes[0]
        imgpath = foil_hole.foil_hole_img
        # Define global variable for use outside def, FoilHole
        global foilpath
        foilpath = imgpath
        # Load FoilHole image
        load = RBGAImage(imgpath)
        width, height = load.size
        print(width, height)
        ratio = width / height
        print(ratio)
        load = load.resize((400, int(400 / ratio)), Image.ANTIALIAS)
        render = ImageTk.PhotoImage(load)
        imgFoil = Label(main_frame, image=render)
        imgFoil.image = render
        imgFoil.place(x=432, y=395)
        # Report selected FoilHole to GUI
        name = os.path.basename(imgpath)
        entryFoil.delete(0, tk.END)
        entryFoil.insert(0, name)
        # Build path for searching for data images
        ## Populate data list box
        # Clear Data list box
        miclist.delete(0, tk.END)
        # Populate listbox
        for item in foil_hole.exposures:
            miclist.insert(tk.END, item)
        ## Print useful information in label
        # Number of FoilHoles images
        lbl = Label(
            main_frame, text="Number of Micrographs: " + str(len(foil_hole.exposures))
        )
        lbl.grid(sticky="w", column=6, row=12)
        clearPickNo()

    def MicSelect(evt):
        value = miclist.get(miclist.curselection())
        imgpath = value
        # Define global variable for use outside def, FoilHole
        global micpath
        micpath = imgpath
        # Load Micrograph image
        load = RBGAImage(imgpath)
        width, height = load.size
        print(width, height)
        ratio = width / height
        print(ratio)
        load = load.resize((400, int(400 / ratio)), Image.ANTIALIAS)
        render = ImageTk.PhotoImage(load)
        imgMic = Label(main_frame, image=render)
        imgMic.image = render
        imgMic.place(x=862, y=395)
        # Report selected data mic to GUI
        name = os.path.basename(imgpath)
        entryMic.delete(0, tk.END)
        entryMic.insert(0, name)
        # Report number of picked particles to GUI
        clearPickNo()
        partLines = []
        global star
        # for line in open(star[1]):
        # for line in open("EPU_analysis/star/.mainDataLines.dat"):
        #    if os.path.splitext(name)[0] in line:
        #        partLines.append(line)
        #        partNo = len(partLines)
        #        lbl = Label(main_frame, text="  " + str(partNo))
        #        lbl.grid(sticky="W", column=8, row=17)
        # Plot particles?
        if pick_state.get() == 1:
            plotPicks(imgpath)

    def radioClickSq():
        value = radioSq.get()
        print("Radio button clicked, use dataset " + value)
        popConditional()

    def radioClickFoil():
        global foilfilt
        foilfilt = radioFoil.get()
        print("Radio button clicked, FoilHole filtering " + foilfilt)

    def detectorSelect():
        detector = combo.get()
        entryMicX.delete(0, tk.END)
        entryMicY.delete(0, tk.END)
        if detector == "K2":
            entryMicX.insert(0, "3710")
            entryMicY.insert(0, "3838")
        elif detector == "K3":
            entryMicX.insert(0, "5760")
            entryMicY.insert(0, "4092")
        elif detector == "FII":
            entryMicX.insert(0, "4096")
            entryMicY.insert(0, "4096")
        elif detector == "FIII":
            entryMicX.insert(0, "4096")
            entryMicY.insert(0, "4096")
        elif detector == "Other":
            entryMicX.insert(0, "")
            entryMicY.insert(0, "")

    def RBGAImage(path):
        return Image.open(path).convert("RGBA")

    def plotPicks(mic_path):
        plot_coords(
            Path(star[1]),
            Path(mic_path),
            int(entryMicX.get()),
            int(entryMicY.get()),
            float(entryPartD.get()),
            Path("./EPU_analysis/star/"),
            flip=(False, True),
        )
        ##Load Micrograph image
        micLoad = RBGAImage(mic_path)
        micLoad = micLoad.resize((400, 400), Image.ANTIALIAS)
        ## Particle pick overlay
        parLoad = RBGAImage("./EPU_analysis/star/particles.png")
        parLoad = parLoad.resize((400, 400), Image.ANTIALIAS)
        micLoad.paste(parLoad, (0, 0), parLoad)
        parRender = ImageTk.PhotoImage(micLoad)
        imgMic = Label(main_frame, image=parRender)
        imgMic.image = parRender
        imgMic.place(x=862, y=395)

    def plotFoilHole():
        square = entrySq.get()
        square = os.path.splitext(mic)[0]
        foil = entryFoil.get()
        foil = os.path.splitext(mic)[0]
        plot_foilhole(str(square) + ".xml", str(foil) + ".xml")
        print("Plotting FoilHole location on Square image")

    def clearPickNo():
        # Clear part picks report
        lbl = Label(main_frame, text="         ")
        lbl.grid(sticky="W", column=8, row=17)

    def clearMicSel():
        ## Clear Mic list box
        miclist.delete(0, tk.END)
        # Clear

    def openSettings():
        try:
            f = open("EPU_analysis/settings.dat")
            print("Populating fields with previous paths")
            for line in f:
                if "Star" in line:
                    global star
                    star = line.strip().split()
                if "EPU" in line:
                    global epu
                    epu = line.strip().split()
                if "Suffix" in line:
                    global suffix
                    suffix = line.strip().split()
            f.close()
        ## Populate fields with defaults if analysis not performed
        except IOError:
            print("Previous analysis not found")

    ###############################################################################

    ### Create GUI
    # main_frame = tk.Tk()
    main_frame = tk.Toplevel()

    main_frame.title("EPU analysis from Relion star file")
    main_frame.geometry("1420x820")

    ## Some defs that need to be run at GUI start
    openSettings()
    clearPickNo()

    ## Variables
    radioSq = StringVar()
    radioFoil = StringVar()
    foilfilt = "foilAll"

    # This scripts location
    exe = sys.argv[0]
    exedir = os.path.dirname(sys.argv[0])

    ## GUI layout
    row = 0
    column = 0

    # btn = tk.Button(main_frame, text="popSquares", command = popSquares).grid(sticky="w", column=2, row=row)
    row += 1

    # Radio buttons for data filtering
    lbl = Label(
        main_frame,
        text="Show all Squares or only Squares found in star file:",
        anchor=W,
        justify=LEFT,
    )
    lbl.grid(column=2, row=row)
    lbl = Label(
        main_frame,
        text="Show all FoilHoles or only FoilHoles with particles:",
        anchor=W,
        justify=LEFT,
    )
    lbl.grid(column=4, row=row)
    row += 1

    rad1 = Radiobutton(
        main_frame,
        text="All",
        indicatoron=0,
        value="squares_all",
        # value="./EPU_analysis/.squares_all.dat",
        command=radioClickSq,
        variable=radioSq,
    ).grid(sticky="w", column=2, row=row)
    rad2 = Radiobutton(
        main_frame,
        text="Used",
        indicatoron=0,
        value="squares_used",
        # value="./EPU_analysis/.squares_used.dat",
        command=radioClickSq,
        variable=radioSq,
    ).grid(sticky="", column=2, row=row)
    rad3 = Radiobutton(
        main_frame,
        text="Not used",
        indicatoron=0,
        value="squares_not_used",
        # value="./EPU_analysis/.squares_not_used.dat",
        command=radioClickSq,
        variable=radioSq,
    ).grid(sticky="e", column=2, row=row)

    rad4 = Radiobutton(
        main_frame,
        text="All",
        indicatoron=0,
        value="foilAll",
        command=radioClickFoil,
        variable=radioFoil,
    ).grid(sticky="w", column=4, row=row)
    rad5 = Radiobutton(
        main_frame,
        text="Used",
        indicatoron=0,
        value="foilUsed",
        command=radioClickFoil,
        variable=radioFoil,
    ).grid(sticky="", column=4, row=row)
    rad6 = Radiobutton(
        main_frame,
        text="Not used",
        indicatoron=0,
        value="foilNot",
        command=radioClickFoil,
        variable=radioFoil,
    ).grid(sticky="e", column=4, row=row)

    row += 1
    lbl = Label(main_frame, text="                                           ")
    lbl.grid(sticky="w", column=4, row=row)

    # Plot picks
    # btn = tk.Button(main_frame,text='Clear picks', command = MicSelect).grid(sticky="e", column=8, row=15)
    pick_state = IntVar()
    pick_state.set(0)  # set check state
    check1 = Checkbutton(main_frame, text="Particles", var=pick_state).grid(
        sticky="e", column=8, row=18
    )

    lbl = Label(main_frame, text="x (px):", anchor=W, justify=LEFT)
    lbl.grid(sticky="w", column=8, row=19)
    entryMicX = tk.StringVar()
    entryMicX = tk.Entry(main_frame, width=5, state="normal")
    entryMicX.grid(column=8, row=19, sticky=E)
    entryMicX.insert(0, "4096")

    lbl = Label(main_frame, text="y (px):", anchor=W, justify=LEFT)
    lbl.grid(sticky="w", column=8, row=20)
    entryMicY = tk.StringVar()
    entryMicY = tk.Entry(main_frame, width=5, state="normal")
    entryMicY.grid(column=8, row=20, sticky=E)
    entryMicY.insert(0, "4096")

    lbl = Label(main_frame, text="D (px):", anchor=W, justify=RIGHT)
    lbl.grid(sticky="w", column=8, row=21)
    entryPartD = tk.StringVar()
    entryPartD = tk.Entry(main_frame, width=5, state="normal")
    entryPartD.grid(column=8, row=21, sticky=E)
    entryPartD.insert(0, "150")

    values = ["K2", "K3", "FII", "FIII", "Other"]
    combo = ttk.Combobox(main_frame, values=values, width=10)
    combo.current(4)
    combo.grid(column=8, row=22)
    combo.bind("<<ComboboxSelected>>", detectorSelect)

    buttonXml = tk.Button(main_frame, text="Inspect xml", command=inspectXml)
    buttonXml.grid(column=8, row=23)

    # btn = tk.Button(main_frame,text='Plot picks', command = plotPicks).grid(sticky="e", column=8, row=16)
    row += 1

    # Labels
    lbl = Label(main_frame, text="Squares:")
    lbl.grid(column=2, row=row)
    lbl = Label(main_frame, text="Foil Holes:")
    lbl.grid(column=4, row=row)
    lbl = Label(main_frame, text="Holes:")
    lbl.grid(column=6, row=row)
    row += 1

    # Listboxs for images
    scrollbar = Scrollbar(main_frame)
    scrollbar.grid(row=row, column=column + 3, rowspan=5, sticky=N + S)
    sqlist = Listbox(main_frame, height=10, width=45, yscrollcommand=scrollbar.set)
    sqlist.grid(row=row, column=column + 2, rowspan=5, sticky=E + W)
    sqlist.bind("<<ListboxSelect>>", SquareSelect)
    scrollbar.config(command=sqlist.yview)
    column += 2

    scrollbar = Scrollbar(main_frame)
    scrollbar.grid(row=row, column=column + 3, rowspan=5, sticky=N + S)
    foillist = Listbox(main_frame, height=10, width=45, yscrollcommand=scrollbar.set)
    foillist.grid(row=row, column=column + 2, rowspan=5, sticky=E + W)
    foillist.bind("<<ListboxSelect>>", FoilSelect)
    scrollbar.config(command=foillist.yview)
    column += 2

    scrollbar = Scrollbar(main_frame)
    scrollbar.grid(row=row, column=column + 3, rowspan=5, sticky=N + S)
    miclist = Listbox(main_frame, height=10, width=45, yscrollcommand=scrollbar.set)
    miclist.grid(row=row, column=column + 2, rowspan=5, sticky=E + W)
    miclist.bind("<<ListboxSelect>>", MicSelect)
    scrollbar.config(command=miclist.yview)
    column += 2

    # Populate lists
    popSquares()

    ## Square image
    sqLoad = Image.open(
        "/".join(epuanalysis.__file__.split("/")[:-1]) + "/../../data/testSq.jpeg"
    )
    sqLoad = sqLoad.resize((400, 400), Image.ANTIALIAS)
    sqRender = ImageTk.PhotoImage(sqLoad)
    imgSq = Label(main_frame, image=sqRender)
    imgSq.image = sqRender
    imgSq.place(x=0, y=395)

    lbl = Label(main_frame, text="Current square selection:", anchor=W, justify=LEFT)
    lbl.grid(sticky="w", column=2, row=10)
    entrySq = tk.StringVar()
    entrySq = tk.Entry(main_frame, width=45, state="normal")
    entrySq.grid(column=2, row=11, sticky=W)

    ## FoilHole image
    fhLoad = RBGAImage(
        "/".join(epuanalysis.__file__.split("/")[:-1]) + "/../../data/testFoil.jpeg"
    )
    fhLoad = fhLoad.resize((400, 400), Image.ANTIALIAS)
    fhRender = ImageTk.PhotoImage(fhLoad)
    imgFoil = Label(main_frame, image=fhRender)
    imgFoil.image = fhRender
    imgFoil.place(x=432, y=395)

    lbl = Label(main_frame, text="Current foil selection:", anchor=W, justify=LEFT)
    lbl.grid(sticky="w", column=4, row=10)
    entryFoil = tk.StringVar()
    entryFoil = tk.Entry(main_frame, width=45, state="normal")
    entryFoil.grid(column=4, row=11, sticky=W)

    ## Micrograph image
    micLoad = RBGAImage(
        "/".join(epuanalysis.__file__.split("/")[:-1]) + "/../../data/testMic.jpeg"
    )
    micLoad = micLoad.resize((400, 400), Image.ANTIALIAS)
    micRender = ImageTk.PhotoImage(micLoad)
    imgMic = Label(main_frame, image=micRender)
    imgMic.image = micRender
    imgMic.place(x=862, y=395)

    lbl = Label(
        main_frame, text="Current micrograph selection:", anchor=W, justify=LEFT
    )
    lbl.grid(sticky="w", column=6, row=10)
    entryMic = tk.StringVar()
    entryMic = tk.Entry(main_frame, width=45, state="normal")
    entryMic.grid(column=6, row=11, sticky=W)

    ## Particle pick overlay
    parLoad = RBGAImage(
        "/".join(epuanalysis.__file__.split("/")[:-1]) + "/../../data/testPart.png"
    )
    parLoad = parLoad.resize((400, 400), Image.ANTIALIAS)
    micLoad.paste(parLoad, (0, 0), parLoad)
    parRender = ImageTk.PhotoImage(micLoad)
    imgMic = Label(main_frame, image=parRender)
    imgMic.image = parRender
    imgMic.place(x=862, y=395)

    main_frame.mainloop()
