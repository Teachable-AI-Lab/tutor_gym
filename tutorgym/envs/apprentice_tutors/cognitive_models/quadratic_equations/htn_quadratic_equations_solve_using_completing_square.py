import sympy as sp
from random import randint, choice

import sympy as sp
from sympy import sstr, latex, symbols
from sympy.parsing.latex._parse_latex_antlr import parse_latex
import re

from random import randint
from shop2.domain import Task, Operator, Method
# from shop2.planner import SHOP2
from shop2.fact import Fact
from shop2.conditions import Filter
from shop2.common import V

    
def htn_quadratic_equations_solve_using_completing_square_problem():
    x = sp.symbols('x')
    b, c = 0, 0
    while not b:
        b, c = randint(-10, 10), randint(1, 10)
    equation = latex(sp.Eq(x**2+b*x, c))
    equation = 'x^{2} - 5 x = 1'
    return equation

def b_by_2_square_lhs(init_value):
    x = symbols('x')
    init_equation = parse_latex(init_value)
    b = init_equation.lhs.expand().coeff(x, 1)
    lhs = parse_latex(f"x^2+{b}x+{(b/2)**2}".replace("+-", "-"))
    answer = re.compile(re.sub(r'([-+()*])', r'\\\1', sp.sstr(lhs, order="grlex")))
    hint = latex(lhs)
    return tuple([(answer, hint)])


def b_by_2_square_rhs(init_value):
    x = symbols('x')
    init_equation = parse_latex(init_value)
    b, c = init_equation.lhs.expand().coeff(x, 1), init_equation.rhs.coeff(x, 0)
    rhs = parse_latex(f"{c}+{(b/2)**2}".replace("+-", "-"))
    answer = re.compile(re.sub(r'([-+()*])', r'\\\1', sp.sstr(rhs, order="grlex")))
    hint = latex(rhs)
    return tuple([(answer, hint)])

def factor_lhs(init_value):
    x = symbols('x')
    init_equation = parse_latex(init_value)
    b = init_equation.lhs.expand().coeff(x, 1)
    factored = parse_latex(f"(x+{b/2})^2".replace("+-", "-"))
    answer = re.compile(re.sub(r'([-+^()*])', r'\\\1', sp.sstr(factored, order="grlex")))
    hint = latex(factored)
    return tuple([(answer, hint)])

def simplify_rhs(init_value):
    x = symbols('x')
    init_equation = parse_latex(init_value)
    b, c = init_equation.lhs.expand().coeff(x, 1), init_equation.rhs.coeff(x, 0)
    simplified = sp.simplify(parse_latex(f"{c}+{(b/2)**2}".replace("+-", "-")))
    answer = re.compile(re.sub(r'([-+()*])', r'\\\1', sp.sstr(simplified, order="grlex")))
    hint = latex(simplified)
    return tuple([(answer, hint)])

def combine_lhs_rhs(init_value):
    x = symbols('x')
    init_equation = parse_latex(init_value)
    b = init_equation.lhs.expand().coeff(x, 1)
    lhs = parse_latex(f"(x+{b/2})^2".replace("+-", "-"))

    init_equation = parse_latex(init_value)
    b, c = init_equation.lhs.expand().coeff(x, 1), init_equation.rhs.coeff(x, 0)
    rhs = sp.simplify(parse_latex(f"{c}+{(b/2)**2}".replace("+-", "-")))
    equation = sp.Eq(lhs, rhs)
    answer = re.compile(re.sub(r'([-+()*])', r'\\\1', sp.sstr(equation, order="grlex")))
    hint = latex(equation)
    return tuple([(answer, hint)])

def positive_root_of_rhs(init_value):
    x = symbols('x')
    init_equation = parse_latex(init_value)
    b, c = init_equation.lhs.expand().coeff(x, 1), init_equation.rhs.coeff(x, 0)
    simplified = sp.simplify(parse_latex(f"{c}+{(b/2)**2}".replace("+-", "-")))

    lhs, rhs = parse_latex(f"x+{b/2}".replace("+-", "-")), simplified
    equation = sp.Eq(lhs, sp.sqrt(rhs))
    answer = re.compile(re.sub(r'([-+()*])', r'\\\1', sp.sstr(equation, order="grlex")))
    hint = latex(equation)
    return tuple([(answer, hint)])

def negative_root_of_rhs(init_value):
    x = symbols('x')
    init_equation = parse_latex(init_value)
    b, c = init_equation.lhs.expand().coeff(x, 1), init_equation.rhs.coeff(x, 0)
    simplified = sp.simplify(parse_latex(f"{c}+{(b/2)**2}".replace("+-", "-")))

    lhs, rhs = parse_latex(f"x+{b/2}".replace("+-", "-")), simplified
    equation = sp.Eq(lhs, -sp.sqrt(rhs))
    answer = re.compile(re.sub(r'([-+()*])', r'\\\1', sp.sstr(equation, order="grlex")))
    hint = latex(equation)
    return tuple([(answer, hint)])

def positive_root(init_value):
    x = symbols('x')
    init_equation = parse_latex(init_value)
    b, c = init_equation.lhs.expand().coeff(x, 1), init_equation.rhs.coeff(x, 0)
    simplified = sp.simplify(parse_latex(f"{c}+{(b/2)**2}".replace("+-", "-")))

    lhs, rhs = parse_latex(f"x+{b/2}".replace("+-", "-")), simplified
    equation = sp.Eq(lhs, sp.sqrt(rhs))
    root = sp.solve(equation, x)[0]
    return tuple([
        (re.compile(re.sub(r'([-+()*])', r'\\\1', sp.sstr(root, order="grlex").replace("*",""))), latex(root)),
        (re.compile(re.sub(r'([-+()*])', r'\\\1', sp.sstr(root, order="grlex"))), latex(root)) 
    ])

def negative_root(init_value):
    x = symbols('x')
    init_equation = parse_latex(init_value)
    b, c = init_equation.lhs.expand().coeff(x, 1), init_equation.rhs.coeff(x, 0)
    simplified = sp.simplify(parse_latex(f"{c}+{(b/2)**2}".replace("+-", "-")))

    lhs, rhs = parse_latex(f"x+{b/2}".replace("+-", "-")), simplified
    equation = sp.Eq(lhs, -sp.sqrt(rhs))
    root = sp.solve(equation, x)[0]
    return tuple([
        (re.compile(re.sub(r'([-+()*])', r'\\\1', sp.sstr(root, order="grlex").replace("*",""))), latex(root)),
        (re.compile(re.sub(r'([-+()*])', r'\\\1', sp.sstr(root, order="grlex"))), latex(root))         
    ])




Domain = {
    'done': Operator(head=('done', V('kc')),
                     precondition=[Fact(start=True)],
                     effects=[Fact(field='done', value=((re.compile('x'),),), kc=V('kc'), answer=True)],
    ),
    'b_by_2_square_lhs': Operator(head=('b_by_2_square_lhs', V('equation'), V('kc')),
                                  precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                                  effects=[Fact(field='b_by_2_square_lhs', value=(b_by_2_square_lhs, V('eq')), kc=V('kc'), answer=True)],
    ),

    'b_by_2_square_rhs': Operator(head=('b_by_2_square_rhs', V('equation'), V('kc')),
                                  precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                                  effects=[Fact(field='b_by_2_square_rhs', value=(b_by_2_square_rhs, V('eq')), kc=V('kc'), answer=True)],
    ),

    'factor_lhs': Operator(head=('factor_lhs', V('equation'), V('kc')),
                           precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                           effects=[Fact(field='factor_lhs', value=(factor_lhs, V('eq')), kc=V('kc'), answer=True)],
    ),

    'simplify_rhs': Operator(head=('simplify_rhs', V('equation'), V('kc')),
                             precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                             effects=[Fact(field='simplify_rhs', value=(simplify_rhs, V('eq')), kc=V('kc'), answer=True)],
    ),

    'combine_lhs_rhs': Operator(head=('combine_lhs_rhs', V('equation'), V('kc')),
                                precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                                effects=[Fact(field='combine_lhs_rhs', value=(combine_lhs_rhs, V('eq')), kc=V('kc'), answer=True)],
    ),

    'positive_root_of_rhs': Operator(head=('positive_root_of_rhs', V('equation'), V('kc')),
                                     precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                                     effects=[Fact(field='positive_root_of_rhs', value=(positive_root_of_rhs, V('eq')), kc=V('kc'), answer=True)],
    ),

    'negative_root_of_rhs': Operator(head=('negative_root_of_rhs', V('equation'), V('kc')),
                                     precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                                     effects=[Fact(field='negative_root_of_rhs', value=(negative_root_of_rhs, V('eq')), kc=V('kc'), answer=True)],
    ),

    'positive_root': Operator(head=('positive_root', V('equation'), V('kc')),
                              precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                              effects=[Fact(field='positive_root', value=(positive_root, V('eq')), kc=V('kc'), answer=True)],
    ),

    'negative_root': Operator(head=('negative_root', V('equation'), V('kc')),
                              precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                              effects=[Fact(field='negative_root', value=(negative_root, V('eq')), kc=V('kc'), answer=True)],
    ),

    'solve': Method(head=('solve', V('equation')),
                    preconditions=[
                        Fact(scaffold='level_3'),
                        Fact(scaffold='level_2'),
                        Fact(scaffold='level_1'),
                        Fact(scaffold='level_0'),
                    ],
                    subtasks=[

                        [
                            Task(head=('b_by_2_square_lhs', V('equation'), ('b_by_2_square_lhs',)), primitive=True),
                            Task(head=('b_by_2_square_rhs', V('equation'), ('b_by_2_square_rhs',)), primitive=True),
                            Task(head=('factor_lhs', V('equation'), ('factor_lhs',)), primitive=True),
                            Task(head=('simplify_rhs', V('equation'), ('simplify_rhs',)), primitive=True),
                            Task(head=('combine_lhs_rhs', V('equation'), ('combine_lhs_rhs',)), primitive=True),
                            Task(head=('positive_root_of_rhs', V('equation'), ('positive_root_of_rhs',)), primitive=True),
                            Task(head=('negative_root_of_rhs', V('equation'), ('negative_root_of_rhs',)), primitive=True),
                            Task(head=('positive_root', V('equation'), ('positive_root',)), primitive=True),
                            Task(head=('negative_root', V('equation'), ('negative_root',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [
                            Task(head=('b_by_2_square_lhs', V('equation'), ('b_by_2_square_lhs',)), primitive=True),
                            Task(head=('b_by_2_square_rhs', V('equation'), ('b_by_2_square_rhs',)), primitive=True),
                            Task(head=('combine_lhs_rhs', V('equation'), ('combine_lhs_rhs',)), primitive=True),
                            Task(head=('positive_root_of_rhs', V('equation'), ('positive_root_of_rhs',)), primitive=True),
                            Task(head=('negative_root_of_rhs', V('equation'), ('negative_root_of_rhs',)), primitive=True),
                            Task(head=('positive_root', V('equation'), ('positive_root',)), primitive=True),
                            Task(head=('negative_root', V('equation'), ('negative_root',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [
                            Task(head=('combine_lhs_rhs', V('equation'), ('combine_lhs_rhs',)), primitive=True),
                            Task(head=('positive_root_of_rhs', V('equation'), ('positive_root_of_rhs',)), primitive=True),
                            Task(head=('negative_root_of_rhs', V('equation'), ('negative_root_of_rhs',)), primitive=True),
                            Task(head=('positive_root', V('equation'), ('positive_root',)), primitive=True),
                            Task(head=('negative_root', V('equation'), ('negative_root',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [
                            Task(head=('positive_root', V('equation'), ('positive_root',)), primitive=True),
                            Task(head=('negative_root', V('equation'), ('negative_root',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],
                    ]
    ),
}