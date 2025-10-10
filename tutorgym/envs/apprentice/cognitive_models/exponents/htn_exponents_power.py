from sympy import latex, sstr
import sympy as sp
from random import randint, choice

import sympy as sp
from sympy.parsing.latex._parse_latex_antlr import parse_latex
import re

from random import randint
from shop2.domain import Task, Operator, Method
# from shop2.planner import SHOP2
from shop2.fact import Fact
from shop2.conditions import Filter
from shop2.common import V

def _safe_parse(expr):
    try:
        return parse_latex(expr)
    except Exception as e:
        raise ValueError(f"Unable to parse expression: {expr}") from e

def _regex_from_sympy(sym):
    return re.compile(re.sub(r'([-+()*^])', r'\\\1', sstr(sym, order="grlex")))

def htn_exponents_power_problem():
    constant = randint(2,1000)
    exponent_1 = randint(2,12)
    exponent_2 = randint(2,12)
    return f"({constant}^{{{exponent_1}}})^{{{exponent_2}}}"
    # return  "(" + str(constant) + "^" + "{" + str(exponent_1) + "})"+ "^" + "{" + str(exponent_2) + "}"


def multiply_values(init_value):
    # (a^m)^n  ->  a^(m*n)  (do NOT evaluate m*n here)
    formula = _safe_parse(init_value)
    base  = formula.args[0].args[0]       # a
    exp1  = formula.args[0].args[1]       # m
    exp2  = formula.args[1]               # n
    answer_sym = sp.Pow(base, sp.Mul(exp1, exp2, evaluate=False), evaluate=False)
    hint_tex   = latex(answer_sym)
    pattern    = _regex_from_sympy(answer_sym)
    return tuple([(pattern, hint_tex)])

def simplify_exp(init_value):
    # a^(m*n)  ->  a^(m*n evaluated)
    formula = _safe_parse(init_value)
    base  = formula.args[0].args[0]       # a
    exp1  = formula.args[0].args[1]       # m
    exp2  = formula.args[1]               # n
    answer_sym = sp.Pow(base, sp.Mul(exp1, exp2, evaluate=True), evaluate=False)
    hint_tex   = latex(answer_sym)
    pattern    = _regex_from_sympy(answer_sym)
    return tuple([(pattern, hint_tex)])

Domain = {
    'done': Operator(head=('done', V('kc')),
                     precondition=[Fact(start=True)],
                     effects=[Fact(field='done', value=((re.compile('x'),),), kc=V('kc'), answer=True)],
    ),

    'multiply_values': Operator(head=('multiply_values', V('equation'), V('kc')),
                                precondition=[Fact(field=V('equation'), value=V('eq'), answer=False)],
                                effects=[Fact(field='multiply_values', value=(multiply_values, V('eq')), kc=V('kc'), answer=True)],
    ),

    'simplify_exp': Operator(head=('simplify_exp', V('equation'), V('kc')),
                            precondition=[Fact(field=V('equation'), value=V('eq'), answer=False)],
                            effects=[Fact(field='simplify_exp', value=(simplify_exp, V('eq')), kc=V('kc'), answer=True)],
    ),

    'solve': Method(head=('solve', V('equation')),
                    preconditions=[
                        Fact(scaffold='level_1'),
                        Fact(field=V('equation'), value=V('eq'), answer=False),
                    ],
                    subtasks=[
                        [
                            Task(head=('multiply_values', V('equation'), ('multiply_values',)), primitive=True),
                            Task(head=('simplify_exp', V('equation'), ('simplify_exp',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [
                            Task(head=('simplify_exp', V('equation'), ('multiply_values', 'simplify_exp')), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],
                    ]
    ),
}
