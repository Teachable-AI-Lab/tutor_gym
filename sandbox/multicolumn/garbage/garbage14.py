from numba import njit, i8
from numba.types import unicode_type
from cre import Var, TF
# from cre import dynamic_exec
from cre.fact import define_fact
from cre.utils import _raw_ptr_from_struct, _raw_ptr_from_struct_incref, _struct_tuple_from_pointer_arr, PrintElapse
from cre.cre_object import CREObjType

BOOP = define_fact("BOOP", {"A" :i8, "B" : unicode_type, 'left' :"BOOP", 'below' :"BOOP", 'right' : "BOOP"})

BOOPProxy = BOOP._fact_proxy


Sel = Var(BOOP, "Sel")

@njit(cache=True)
def foo(a,b,c):
    # print(v.left.below.below.below, v.right.below)
    tup1 = TF(a, b)#.asa(CREObjType) 
    tup2 = TF(a, c)#.asa(CREObjType)
    print(tup1)
    print(tup2)

    print(tup1==tup2)
    print(hash(tup1), hash(tup2))

# print()
foo(Sel.left.below.below.below, Sel.right.below, Sel.below.below.right)

