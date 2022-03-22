import tkinter as tk
import os

from PIL import ImageTk, Image

from itertools import count
from typing import Callable, Dict, Optional, Tuple, Union

from epuanalysis.scale import ImageScale


class GUIFrame:
    def __init__(
        self,
        title: str,
        geometry: str = "650x300",
        top_level: bool = False,
        start_loop: bool = False,
    ):
        if top_level:
            self.frame = tk.Toplevel()
        else:
            self.frame = tk.Tk()
        self.frame.title(title)
        self.frame.geometry(geometry)
        self._counter = count(start=1)
        self._entries: Dict[str, Union[tk.Entry, tk.StringVar]] = {}
        self._image_scales: Dict[str, ImageScale] = {}
        self._image_locs: Dict[str, Tuple[int, int]] = {}
        if start_loop:
            self._generate_items()
            self.frame.mainloop()

    def _generate_items(self):
        raise NotImplementedError(
            "The _generate_items class method should be declared fro subclasses of GUIFrame"
        )

    def row(self):
        return next(self._counter)

    def _make_button(
        self,
        row: int,
        text: str,
        command: Callable,
        var: Optional[tk.StringVar] = None,
        columns: Tuple[int, int] = (1, 0),
    ) -> tk.Entry:
        if var:
            entry = tk.Entry(self.frame, width=40, textvariable=var)
        else:
            entry = tk.Entry(self.frame, width=40, state="normal")
        entry.grid(column=columns[0], row=row)
        button = tk.Button(self.frame, text=text, command=command)
        button.grid(column=columns[1], row=row)
        return entry

    def _make_label(
        self,
        row: int,
        text: str,
        column_entry: int = 1,
        column_label: int = 0,
        width: int = 40,
        var: Optional[tk.StringVar] = None,
        sticky: str = "",
    ) -> tk.Entry:
        if var:
            entry = tk.Entry(self.frame, width=40, textvariable=var)
        else:
            entry = tk.Entry(self.frame, width=40)
        entry.grid(column=column_entry, row=row, sticky=sticky)
        lbl = tk.Label(self.frame, text=text)
        lbl.grid(column=column_label, row=row)
        return entry

    def add_scale(self, imsc: ImageScale, imloc: Tuple[int, int]):
        self._image_scales[imsc.name] = imsc
        self._image_locs[imsc.name] = imloc

    def draw_scale(
        self,
        imname: str,
        entry: str = "",
        reset_entry: str = "",
        img_override: Optional[Image.Image] = None,
    ):
        load = img_override or self._image_scales[imname].pil_image
        width, height = load.size
        ratio = width / height
        load = load.resize((400, int(400 / ratio)), Image.ANTIALIAS)
        render = ImageTk.PhotoImage(load)
        self._entries[imname] = tk.Label(self.frame, image=render)
        self._entries[imname].image = render
        self._entries[imname].place(
            x=self._image_locs[imname][0], y=self._image_locs[imname][1]
        )
     
        if reset_entry:
            self._entries[reset_entry].delete(0, tk.END)
        if entry:
            name = os.path.basename(self._image_scales[imname].image)
            self._entries[entry].delete(0, tk.END)
            self._entries[entry].insert(0, name)
        for k, abv in self._image_scales[imname].above.items():
            curr_scale = self._image_scales[imname]
            iov = curr_scale.mark_image(
                (curr_scale.cx, curr_scale.cy), scale_shift=1, target_tag=k
            )
            self.draw_scale(abv.name, img_override=iov)
