from functools import singledispatch
from typing import Union

from epuanalysis.tracking import FoilHole, GridSquare

@singledispatch
def aggregate_scalar(top_level, key: str) -> Union[float, int]:
    raise NotImplementedError(f"aggregate_scalar not implemented for {type{top_level}}")

@aggregate_scalar
def _(top_level: GridSquare, key: str) -> Union[float, int]:
    total = 0
    for fh in top_level.foil_holes:
        for ex in fh.exposures:
            total += ex[1][key]
    return total

@aggregate_scalar
def _(top_level: FoilHole, key: str) -> Union[float, int]:
    total = 0
    for ex in fh.exposures:
        total += ex[1][key]
    return total
