from functools import singledispatchmethod
from typing import Any, Dict

class _BaseFrame:
    def __init__(self, title: str):
        self.title = title
        self.vars: Dict[str, Any] = {}
        self.children: Dict[str, _BaseFrame] = {}

    @singledispatchmethod
    def add_component(self, comp):
        raise NotImplementedError(f"add_component not implemented for {comp}")
    
    def update(self):
        for ch in self.children.values():
            ch.update()
            