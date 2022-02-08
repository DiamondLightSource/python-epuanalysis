#!/usr/bin/env python
#

# This code is adapted from a python script kindly shared by T.J.Ragen - University of Leciester, 2019

import os
import sys
import xml.etree.ElementTree as ET

import matplotlib
import matplotlib.pyplot as plt

# FEI EPU xml stuff
ns = {
    "p": "http://schemas.datacontract.org/2004/07/Applications.Epu.Persistence"
}  # TODO: versioning
ns["system"] = "http://schemas.datacontract.org/2004/07/System"
ns["so"] = "http://schemas.datacontract.org/2004/07/Fei.SharedObjects"
ns["g"] = "http://schemas.datacontract.org/2004/07/System.Collections.Generic"
ns["s"] = "http://schemas.datacontract.org/2004/07/Fei.Applications.Common.Services"
ns["a"] = "http://schemas.datacontract.org/2004/07/System.Drawing"

# Define functions
def xml_parse(filein):
    # Read xml file for square
    tree = ET.parse(filein)
    root = tree.getroot()
    # Find stage positions in xml file
    stage_position_x = root.find("so:microscopeData/so:stage/so:Position/so:X", ns).text
    stage_position_y = root.find("so:microscopeData/so:stage/so:Position/so:Y", ns).text
    pixel_size = root.find("so:SpatialScale/so:pixelSize/so:x/so:numericValue", ns).text
    # Return variables from function
    # Remember variables cease to exist outside of function
    return (
        float(stage_position_x) * 1e6,
        float(stage_position_y) * 1e6,
        float(pixel_size) * 1e6,
    )


################################################################################


def plot_foilhole(xml_square: str, xml_foilhole: str):

    # Get variables from xml file
    sq_micron_x, sq_micron_y, sq_micron_pix = xml_parse(xml_square)
    fh_micron_x, fh_micron_y, fh_micron_pix = xml_parse(xml_foilhole)

    # Calculate FoilHole location on Square in microns
    fh_loc_micron_x = sq_micron_x - fh_micron_x
    fh_loc_micron_y = sq_micron_y - fh_micron_y
    # Convert to pixels
    fh_loc_px_x = fh_loc_micron_x / sq_micron_pix
    fh_loc_px_y = fh_loc_micron_y / sq_micron_pix
    # Convert to pixel coordinates based on detector size
    fh_plot_px_x = 2048 + fh_loc_px_x
    fh_plot_px_y = 2048 - fh_loc_px_y

    print(fh_plot_px_x)
    print(fh_plot_px_y)

    ################################################################################

    # Plot coordinate to file to display as overlay on square image
    fig = plt.figure(figsize=(1024 / 100.0, 1024 / 100.0), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim([0, 4096])
    ax.set_ylim([0, 4096])
    ax.axis("off")

    ax.scatter(fh_plot_px_x, fh_plot_px_y, facecolors="none", edgecolors="r", s=300)
    plt.savefig("FoilHole.png", bbox_inches=0, transparent="True")
