import tkinter as tk
from pathlib import Path
from functools import partial
from epuanalysis.tracking import EPUTracker
from epuanalysis.gui import _BaseFrame
from epuanalysis.gui.tk import (
    button,
    button_with_entry,
    label_with_entry,
    file_search,
    _GridEntry,
)
from epuanalysis.gui.tk.inspector import InspectorFrame
from epuanalysis.gui.tk.distributions import DistributionLoader
from typing import Dict, NamedTuple, Optional, Tuple


class StartupFrame(_BaseFrame):
    def __init__(self, title: str, geometry: str = "650x300"):
        super().__init__(title)
        self.frame = tk.Tk()
        self.frame.title(self.title)
        self.frame.geometry(geometry)
        self._grid: Dict[str, _GridEntry] = {
            "epu_dir": _GridEntry((0, 0), None),
            "suffix": _GridEntry((1, 0), None),
            "atlas": _GridEntry((2, 0), None),
            "inspect_button": _GridEntry((3, 1), None),
            "dist_button": _GridEntry((4, 1), None),
        }

        self.vars["epu_dir"] = button_with_entry(
            self.frame,
            file_search,
            self._grid["epu_dir"].position,
            var=tk.StringVar(),
            text="Browse EPU",
        )

        self.vars["suffix"] = label_with_entry(
            self.frame,
            self._grid["suffix"].position,
            var=tk.StringVar(),
            text="Micrograph suffix",
        )

        self.vars["atlas"] = button_with_entry(
            self.frame,
            file_search,
            self._grid["atlas"].position,
            var=tk.StringVar(),
            text="Browse Atlas image",
            directory=False,
        )

        button(
            self.frame,
            self._launch_inspector,
            self._grid["inspect_button"].position,
            text="Inspect images",
        )
        # button(self.frame, self._load_distributions, self._grid["dist_button"].position, text="Load data")

        self.frame.mainloop()

    def _load_distributions(self):
        self.children["dist_loader"] = DistributionLoader("Data loader")

    def _launch_inspector(self):
        tracker = EPUTracker(
            Path("."),
            Path(self.vars["epu_dir"].get()),
            suffix=self.vars["suffix"].get(),
            # starfile=starpath,
            # column=column,
            atlas=Path(self.vars["atlas"].get()),
        )
        data = tracker.track()["squares_all"]
        self.children["inspector"] = InspectorFrame("EPU analysis", data=data)


if __name__ == "__main__":
    StartupFrame("Test startup")
