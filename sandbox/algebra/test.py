
from apprentice.agents.cre_agents.funcs import CREFunc, f8, string, boolean 
import cloudpickle
from algebra_funcs import (ReverseSign, ExprVar, EvalArithmetic,
    AddTerm,  DivTerm, MulTerm, ExprConst,
    ExprCoeff, WriteMultiply, WriteDivide, WriteSubtract, WriteAdd,
    pair_like_terms, _sum_coeffs, term_type, float_to_str, terms_to_str)

import cre
from tutorenvs.algebra_std import Algebra
from numba import njit
from numba.types import Tuple, ListType, optional
from numba.typed import List, Dict 
from cre.utils import PrintElapse


# @CREFunc(signature=string(string, string))
def SubtractTerm(x,y):
    terms_pairs = pair_like_terms(x, y)
    print(terms_pairs)
    new_terms = List.empty_list(term_type)
    for (v,dv), (terms_x, terms_y) in terms_pairs.items():
        c0, c1 = _sum_coeffs(terms_x), _sum_coeffs(terms_y)
        ss = float_to_str(c0-c1)
        if(dv != ""):
            new_terms.append((ss, "", "", dv))
        else:
            new_terms.append((ss, v, "", ""))
    return terms_to_str(new_terms)

print(ExprConst("7y+(-6)"))
print(SubtractTerm("-7", ExprConst("7y+(-6)")))
# print(cloudpickle.dumps(py_func))
