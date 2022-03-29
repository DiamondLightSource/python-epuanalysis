import tkinter as tk
from functools import partial
from epuanalysis.gui import _BaseFrame
from epuanalysis.gui.tk import button, button_with_entry, label_with_entry, file_search
from typing import Dict, NamedTuple, Optional, Tuple


class DistributionLoader(_BaseFrame):
    def __init__(self, title: str, geometry: str = "650x300"):
        super().__init__(title)
        self.frame = tk.Toplevel()
        self.frame.title(self.title)
        self.frame.geometry(geometry)
