import tkinter as tk

from itertools import count
from typing import Callable, Dict, Optional, Tuple, Union


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
