import numpy as np
from numba import njit
import cre

@njit(cache=True)
def round_it(x):
    return str(round(x, 6))

print(round_it(2/3))
