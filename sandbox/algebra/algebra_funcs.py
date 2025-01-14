import cre
from tutorenvs.algebra_std import Algebra
from numba import njit
from numba.types import Tuple, ListType, optional
from numba.typed import List, Dict 

from apprentice.agents.cre_agents.funcs import CREFunc, f8, string, boolean 
from cre.type_conv import float_to_str as jit_str


#0821a 275f9
@CREFunc(signature=string(string))
def ReverseSign(x):
    fx = -float(x)
    return str(x)
# print(-6.0)
# print(7.0)


@njit(cache=True)
def has_alpha(x):
    for c in x:
        o = ord(c)
        if(o >= 65 and o <= 122): # if in [a-zA-Z]
            return True
    return False


@njit(cache=True)
def sep_term_strs(x):
    # Strip whitespace
    x = x.replace(" ", "")

    if(x == ""):
        raise ValueError()

    terms_strs = List()
    i = j = 0
    L = len(x)
    while i < L:
    # for i in range(len(x)):
        skip = -1
        if(x[i:i+3] == ")+("):
            skip = 3
        elif(x[i:i+2] == ")+"):
            skip = 2
        elif(x[i:i+2] == "+("):
            skip = 2
        elif(x[i:i+1] == ")"):
            # not end of term if next char is variable
            if(i+1 >= L or not has_alpha(x[i+1])):
                skip = 1
        elif(x[i:i+1] == "+"):
            skip = 1
        elif(i != 0 and x[i:i+1] == "-"
             and x[i-1] not in ("/","(")):
            terms_strs.append(x[j:i])
            j = i
        elif(i == 0 and x[i:i+1] == "("):
            # Skip Leading "("
            j += 1
        elif(i != 0 and has_alpha(x[i]) and has_alpha(x[i-1])):
            # variables should only be one character
            raise ValueError()

        if(skip != -1):
            terms_strs.append(x[j:i])
            i = j = i+skip
        else:
            i += 1
    if(i != j): 
        terms_strs.append(x[j:i])

    for i, ts in enumerate(terms_strs):
        terms_strs[i] = ts.replace(")", "").replace("(", "")
    return terms_strs

@njit(cache=True)
def sep_monomial(x):
    var = ""
    o = ord(x[-1])
    if(o >= 65 and o <= 122): # if in [a-zA-Z]
        var = x[-1]
        x = x[:-1]
    if(x == "-"):
        x = "-1"
    if(x == ""):
        x = "1"
    return x, var

@njit(cache=True)
def sep_terms(x):
    strs = sep_term_strs(x)
    terms = List()
    for s in strs:
        lst = s.split("/")
        coeff, var, dcoeff, dvar = "", "", "", ""
        if(len(lst) == 2):
            dcoeff, dvar = sep_monomial(lst[1])
        coeff, var = sep_monomial(lst[0])
        if(not has_alpha(coeff) and not has_alpha(dcoeff)):
            terms.append((coeff, var, dcoeff, dvar))
    return terms

IGNORE_1_COEFF = True
IGNORE_NEG1_COEFF = True

@njit(cache=True)
def term_to_str(term):
    c, v, dc, dv = term
    if(v != ""):
        if(IGNORE_1_COEFF and c == "1"):
            c = ""
        elif(IGNORE_NEG1_COEFF and c == "-1"):
            c = "-"

    if(dv != ""):
        if(IGNORE_1_COEFF and dc == "1"):
            dc = ""
        elif(IGNORE_NEG1_COEFF and dc == "-1"):
            dc = "-"

    s = ""
    if(dc != "" or dv != ""):
        s = f'{c}{v}/{dc}{dv}'
    else:
        s = f'{c}{v}'
    return s

@njit(cache=True)
def is_neg(term):
    return len(term) > 0 and term[0] == "-"

#4e765, #97a89
@njit(cache=True)
def terms_to_str(terms):  
    # Put the constant terms last
    var_terms = List()
    const_terms = List()
    for term in terms:
        c, v, dc, dv = term
        if(v == "" and dv == ""):
            const_terms.append(term)
        else:
            var_terms.append(term)
    terms = [*var_terms,*const_terms]

    all_zero = True
    lst = List()
    for i, term in enumerate(terms):
        c, v, dc, dv = term

        # Drop zero terms
        if(v == "" and (c == "0" or c == "") and 
           dv == "" and (dc == "0" or dc == "")):
            continue

        all_zero = False
        ts = term_to_str(term)

        if(i!=0 and (is_neg(c) or is_neg(dc) or is_neg(dv))):
            ts = f"({ts})"
        if(ts):
            lst.append(ts)
    if(all_zero):
        return "0"
    return "+".join(lst)


@njit(cache=True)
def insert_like_terms(like_terms, terms):
    for c, v, dc, dv in terms:
        tup = (v, dv)
        if(tup not in like_terms):
            like_terms[tup] = List.empty_list(term_type)    
        like_terms[tup].append((c,v,dc,dv))
@njit(cache=True)
def term_coef_as_decimal(term):
    c,v,dc,dv = term
    if(c == ""):
        c = "1"
    if(dc != ""):
        return float(c)/float(dc)
    else:
        return float(c)

@njit(cache=True)
def float_to_str(x):
    if(x % 1.0 == 0):
        return str(int(x))
    else:
        return str(round(x,6))
@njit(cache=True)
def _sum_coeffs(terms):
    _sum = 0.0
    for term in terms:            
        _sum += term_coef_as_decimal(term)
    return _sum

#b60ed da911
#** EvalArithmetic 124ee
#(unicode_type,) -> unicode_type, ctx=-7a26b4637c368f32, code=b60ed, closure=e3b0c


var_pair = Tuple((string, string))
term_type = Tuple((string, string, string, string))
term_list = ListType(term_type)
@CREFunc(signature=string(string))
def EvalArithmetic(x):
    like_terms = Dict.empty(var_pair, term_list)
    terms = sep_terms(x)
    insert_like_terms(like_terms, terms)

    new_terms = List.empty_list(term_type)
    for (v, dv), terms in like_terms.items():
        _sum = _sum_coeffs(terms)
        sum_str = float_to_str(_sum)
        if(dv != ""):
            new_terms.append((sum_str, "", "", dv))
        else:
            new_terms.append((sum_str, v, "", ""))

    return terms_to_str(new_terms)

# raise ValueError()

# pairs_type = Tuple((,optional(term_type)))
@njit(cache=True)
def pair_like_terms(x, y):
    like_terms_x = Dict.empty(var_pair, term_list)
    terms_x = sep_terms(x)
    insert_like_terms(like_terms_x, terms_x)

    like_terms_y = Dict.empty(var_pair, term_list)
    terms_y = sep_terms(y)
    insert_like_terms(like_terms_y, terms_y)

    pairs = Dict()
    for v_tup, terms in like_terms_x.items():
        if(v_tup in like_terms_y):
            pairs[v_tup] = (terms, like_terms_y[v_tup])
        else:
            pairs[v_tup] = (terms, List.empty_list(term_type))

    for v_tup, terms in like_terms_y.items():
        if(v_tup not in like_terms_x):
            pairs[v_tup] = (List.empty_list(term_type), terms)            

    return pairs

@CREFunc(signature=string(string, string))
def AddTerm(x,y):
    terms_pairs = pair_like_terms(x, y)
    new_terms = List.empty_list(term_type)
    for (v,dv), (terms_x, terms_y) in terms_pairs.items():
        if(len(terms_y) == 0):
            for t in terms_x:
                new_terms.append(t)
            continue
        c0, c1 = _sum_coeffs(terms_x), _sum_coeffs(terms_y)
        ss = float_to_str(c0+c1)
        if(dv != ""):
            new_terms.append((ss, "", "", dv))
        else:
            new_terms.append((ss, v, "", ""))
    return terms_to_str(new_terms)


@CREFunc(signature=string(string, string))
def SubTerm(x,y):
    terms_pairs = pair_like_terms(x, y)
    new_terms = List.empty_list(term_type)
    for (v,dv), (terms_x, terms_y) in terms_pairs.items():
        if(len(terms_y) == 0):
            for t in terms_x:
                new_terms.append(t)
            continue
        c0, c1 = _sum_coeffs(terms_x), _sum_coeffs(terms_y)
        ss = float_to_str(c0-c1)
        if(dv != ""):
            new_terms.append((ss, "", "", dv))
        else:
            new_terms.append((ss, v, "", ""))
    return terms_to_str(new_terms)


@njit(cache=True)
def _is_const(term):
    if(term[1] != "" or
        term[3] != ""
       ):
            return False
    return True

@njit(cache=True)
def _is_single_const(terms):
    if(len(terms) != 1):
        return False
    
    return _is_const(terms[0])



@CREFunc(signature=string(string, string))
def DivTerm(x, y):
    terms_x = sep_terms(x)
    terms_y = sep_terms(y)

    # Ensure y is just a constant
    if(not _is_single_const(terms_y)):
        raise Exception

    y_val = term_coef_as_decimal(terms_y[0])

    new_terms = List.empty_list(term_type)
    for term in terms_x:
        c, v, dc, dv = term
        _v = v if v != "" else dv
        c = term_coef_as_decimal(term) / y_val
        ss = float_to_str(c)
        new_terms.append((ss, _v, "", ""))
    return terms_to_str(new_terms)

@CREFunc(signature=string(string, string))
def MulTerm(x, y):
    terms_x = sep_terms(x)
    terms_y = sep_terms(y)

    new_terms = List.empty_list(term_type)
    for term_x in terms_x:
        # x_const = _is_const(term_x)
        for term_y in terms_y:
            # var_term = term_x if not x_const else term_y
            # coeff_term = term_y if not x_const else term_x
            c0, v0, dc0, dv0 = term_x
            c1, v1, dc1, dv1 = term_y
            _v  = v0 or v1
            _dv = dv0 or dv1
            # Cancel out case
            if((v0 != "" and v0 == dv1) or
               (v1 != "" and v1 == dv0)):
                _v = ""  
                _dv = ""
            # _v = v if v != "" else dv
            c = term_coef_as_decimal(term_x) * term_coef_as_decimal(term_y)
            ss = float_to_str(c)
            new_terms.append((ss, _v, "", _dv))

    return terms_to_str(new_terms)



@CREFunc(signature=string(string))
def ExprConst(x):
    terms = sep_terms(x)
    # print("$$", terms)
    const_terms = [term for term in terms if _is_const(term)]
    if(len(const_terms) == 1):
        c, v, dc, dv = const_terms[0]
        if(not v and not dv):
            return terms_to_str(const_terms)
    raise ValueError()
    

@CREFunc(signature=string(string))
def ExprCoeff(x):
    terms = sep_terms(x)
    coeff_terms = [term for term in terms if not _is_const(term)]
    if(len(coeff_terms) == 1):
        c, v, dc, dv = coeff_terms[0]
        return terms_to_str(List([(c, "", dc, "")]))
    raise ValueError()


@CREFunc(signature=string(string))
def ExprDenCoeff(x):
    terms = sep_terms(x)
    coeff_terms = [term for term in terms if not _is_const(term)]
    if(len(coeff_terms) == 1):
        c, v, dc, dv = coeff_terms[0]
        return terms_to_str(List([(dc, "", "", "")]))
    raise ValueError()

@CREFunc(signature=string(string))
def Numerator(x):
    terms = sep_terms(x)
    if(len(terms) == 1):
        c, v, dc, dv = terms[0]
        return terms_to_str(List([(c, v, "", "")]))
    raise ValueError()


@CREFunc(signature=string(string))
def Denominator(x):
    terms = sep_terms(x)
    if(len(terms) == 1):
        c, v, dc, dv = terms[0]
        return terms_to_str(List([(dc, dv, "", "")]))
    raise ValueError()

@CREFunc(signature=string(string))
def ExprVar(x):
    terms = sep_terms(x)
    var_terms = [term for term in terms if not _is_const(term)]
    if(len(var_terms) == 1):
        c, v, dc, dv = var_terms[0]
        if(dv):
            return terms_to_str(List([("", dv, "", "")]))
        else:
            return terms_to_str(List([("", v, "", "")]))
    raise ValueError()


@CREFunc(signature=string(string))
def FirstTerm(x):
    terms = sep_terms(x)
    return terms_to_str([terms[0]])


@CREFunc(signature=string(string))
def LastTerm(x):
    terms = sep_terms(x)
    return terms_to_str([terms[-1]])

@CREFunc(signature=string(string))
def GetOperand(x):
    arr = x.split(" ")
    if(len(arr) !=2 or 
        arr[0] not in ("multiply", "divide", "subtract", "add")):
        raise ValueError()
    return arr[1]

@CREFunc(signature=string(string))
def GetOperator(x):
    arr = x.split(" ")
    if(len(arr) !=2 or 
        arr[0] not in ("multiply", "divide", "subtract", "add")):
        raise ValueError()
    return arr[0]

# print(">>", sep_terms("subtract -8"))
# print(">>", SubTerm(Numerator("4"), "subtract -8"))
# print(">>", SubTerm("-5-1y", GetOperand("subtract -5")) )
# print(">>", SubTerm("-9+x/4", GetOperand("subtract -9")) )

# print(">>", AddTerm("4x-2", GetOperand("add 2")))
# print(">>", SubTerm("4x+2", GetOperand("subtract 2")))
# print(">>", DivTerm("-2.5x", GetOperand("divide -2.5")))
print(">>", MulTerm("x/-2", GetOperand("multiply -2")))
print(">>", MulTerm("9/x", GetOperand("multiply x")))

@CREFunc(signature=string(string))
def WriteMultiply(x):
    return f"multiply {x}"

@CREFunc(signature=string(string))
def WriteDivide(x):
    return f"divide {x}"

@CREFunc(signature=string(string))
def WriteSubtract(x):
    return f"subtract {x}"

@CREFunc(signature=string(string))
def WriteAdd(x):
    return f"add {x}"


# print(">>", Denominator("-2/x"))
# print("!>>", ExprCoeff("-y"))
# print("?>>", WriteMultiply(ExprDenCoeff("-5=9+x/4")))
# print(">>", SubTerm(WriteAdd("2/x"), "multiply x"))




if __name__ == "__main__":


    print("----------------")
    print(AddTerm("5", "-3y+(-4)"))
    # raise ValueError()
    # Sanity check
    if(False):
        for prob_name in Algebra().problems:
            seps = [sep_terms(x) for x in prob_name.split('=')]
            rec = "=".join([terms_to_str(s) for s in seps])
            if(prob_name != rec):
                print(prob_name, rec)
                print([tuple(list(x)) for x in seps])

    assert AddTerm("3x+4", "5x+(-2)") == "8x+2"
    assert AddTerm("2", "5x-2") == "5x"

    assert SubTerm("3x+4", "5x+(-2)") == "-2x+6"
    assert SubTerm("2", "5x-2") == "-5x+4"
    assert SubTerm("5x+2", "2") == "5x"
    assert SubTerm("-7", "2") == "-9"

    assert DivTerm("4x+4", "2") == "2x+2"
    assert DivTerm("x/2+4", "2") == "0.25x+2"

    assert MulTerm("4x+4", "2") == "8x+8"
    assert MulTerm("x/2+4", "2") == "x+8"
    assert MulTerm("-3", "x") == "-3x"

    assert ExprConst("3x+6") == "6"
    assert ExprConst("(-3/6)x+(-3/4)") == "-3/4"
    assert ExprConst("-3x/6-3/4") == "-3/4"

    assert ExprCoeff("3x+6") == "3"
    assert ExprCoeff("(-3/6)x+(-3/4)") == "-3/6"
    assert ExprCoeff("-3x/6-3/4") == "-3/6"

    assert FirstTerm("3x+6") == "3x"
    assert LastTerm("3x+6") == "6"

    
    # SubTerm()

    # raise ValueError()



# print(ExprConst("3x+1"))
# print(ExprConst("3/x-2"))
# print(ExprConst("7.2/x-2"))
# print(ExprConst("-7.2/x-2"))
# print(ExprConst("-7.992y+55"))



