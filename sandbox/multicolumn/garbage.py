from numba import njit
from numba.typed import Dict, List

@njit(nogil=True)
def foo():
    d = Dict()
    d[3] = 1
    print(d) # <- Only segfaults with this
    # x = 0
    # for k in d:
    #     x += k
    # return x
foo()
# foo.inspect_llvm()
for v, k in foo.inspect_asm().items():
    print(v, k)

