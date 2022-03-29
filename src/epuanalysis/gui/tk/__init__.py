import os
import tkinter as tk
from tkinter import filedialog
from functools import partial
from typing import Callable, Dict, NamedTuple, Tuple, Optional
from PIL import ImageTk, Image
from epuanalysis.scale import ImageScale


class _GridEntry(NamedTuple):
    position: Tuple[int, int]
    size: Optional[Tuple[int, int]]


def file_search(entry: tk.Entry, directory: bool = True) -> str:
    if directory:
        f = filedialog.askdirectory(initialdir=".", title="Select directory")
    else:
        f = filedialog.askopenfilename(
            initialdir=".",
            title="Select file",
            filetypes=(("all files", "*.*"), ("star files", "*.star")),
        )
    entry.delete(0, tk.END)
    entry.insert(0, f)
    return f


def button_with_entry(
    frame: tk.Tk,
    callback: Callable,
    position: Tuple[int, int],
    var: Optional[tk.StringVar] = None,
    text: str = "",
    width: int = 40,
    directory: bool = True,
) -> tk.Entry:
    if var:
        entry = tk.Entry(frame, width=width, textvariable=var)
    else:
        entry = tk.Entry(frame, width=width, state="normal")
    entry.grid(column=position[1] + 1, row=position[0])
    button = tk.Button(
        frame, text=text, command=partial(callback, entry, directory=directory)
    )
    button.grid(column=position[1], row=position[0])
    return entry


def button(
    frame: tk.Tk, callback: Callable, position: Tuple[int, int], text: str = ""
) -> None:
    button = tk.Button(frame, text=text, command=callback)
    button.grid(column=position[1], row=position[0])


def label_with_entry(
    frame: tk.Tk,
    position: Tuple[int, int],
    var: Optional[tk.StringVar] = None,
    text: str = "",
    width: int = 40,
) -> tk.Entry:
    if var:
        entry = tk.Entry(frame, width=width, textvariable=var)
    else:
        entry = tk.Entry(frame, width=width)
    entry.grid(column=position[1] + 1, row=position[0], sticky="e")
    lbl = tk.Label(frame, text=text)
    lbl.grid(column=position[1], row=position[0])
    return entry


def selection_box(
    frame: tk.Tk, position: Tuple[int, int], size: Tuple[int, int], callback: Callable
) -> tk.Listbox:
    scrollbar = tk.Scrollbar(frame)
    scrollbar.grid(row=position[0], column=position[1] + 3, rowspan=5, sticky="ns")
    lb = tk.Listbox(frame, height=size[0], width=size[1], yscrollcommand=scrollbar.set)
    lb.grid(row=position[0], column=position[1] + 2, rowspan=5, sticky="ew")
    lb.bind("<<ListboxSelect>>", callback)
    scrollbar.config(command=lb.yview)
    return lb


def tk_image(
    frame: tk.Tk, imscale: ImageScale, imlocations: Dict[str, _GridEntry]
) -> tk.Label:
    load = imscale.pil_image
    width, height = load.size
    ratio = width / height
    load = load.resize(
        (
            imlocations[imscale.name].size[0],
            int(imlocations[imscale.name].size[0] / ratio),
        ),
        Image.ANTIALIAS,
    )
    render = ImageTk.PhotoImage(load)
    label = tk.Label(frame, image=render)
    label.image = render
    label.place(
        x=imlocations[imscale.name].position[0],
        y=imlocations[imscale.name].position[1],
    )
    return label


def draw_scale(
    frame: tk.Tk,
    imscale: ImageScale,
    label: tk.Label,
    scale_locations: Dict[str, _GridEntry],
    entry: Optional[tk.Entry] = None,
    reset_entry: Optional[tk.Entry] = None,
    img_override: Optional[Image.Image] = None,
) -> None:
    load = img_override or imscale.pil_image
    width, height = load.size
    ratio = width / height
    load = load.resize(
        (
            scale_locations[imscale.name].size[0],
            int(scale_locations[imscale.name].size[0] / ratio),
        ),
        Image.ANTIALIAS,
    )
    render = ImageTk.PhotoImage(load)
    label = tk.Label(frame, image=render)
    label.image = render
    label.place(
        x=scale_locations[imscale.name].position[0],
        y=scale_locations[imscale.name].position[1],
    )

    if reset_entry:
        reset_entry.delete(0, tk.END)
    if entry:
        name = os.path.basename(imscale.image)
        entry.delete(0, tk.END)
        entry.insert(0, name)
    for k, abv in imscale.above.items():
        curr_scale = imscale
        iov = curr_scale.mark_image(
            (curr_scale.cx, curr_scale.cy), scale_shift=1, target_tag=k
        )
        if abv._frame:
            draw_scale(abv._frame, abv, scale_locations, img_override=iov)
        else:
            draw_scale(frame, abv, scale_locations, img_override=iov)
