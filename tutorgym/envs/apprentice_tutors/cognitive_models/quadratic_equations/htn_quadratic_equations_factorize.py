import sympy as sp
from random import randint, choice

import sympy as sp
from sympy import sstr, latex, expand, symbols
from sympy.parsing.latex._parse_latex_antlr import parse_latex
import re

from random import randint
from shop2.domain import Task, Operator, Method
# from shop2.planner import SHOP2
from shop2.fact import Fact
from shop2.conditions import Filter
from shop2.common import V

from htn_cognitive_models import HTNCognitiveModel
from htn_cognitive_models import htn_loaded_models
from studymaterial import studymaterial
  
def htn_quadratic_equations_factorize_problem():
    x = sp.symbols('x')
    x1, x2, coeff = 0, 0, 0
    while not (x1*x2) or not coeff:
      x1, x2 = randint(-10, 10), randint(-10, 10)
      factorlist = [f for factor in sp.divisors(int(x1)) for f in (factor, -factor) if (f*x2+x1)]
      if factorlist: 
        coeff = choice(factorlist)
    equation = f"{latex(expand((coeff*x-x1) * (x-x2)))}=0"
    return equation


def b_value(init_value):
    x = symbols('x')
    equation = sp.simplify(parse_latex(init_value.split("=")[0]))
    answer = re.compile(str(equation.coeff(x, 1)))
    hint = str(equation.coeff(x, 1))
    value = tuple([(answer, hint)])
    return value

def ac_value(init_value):
    x = symbols('x')
    equation = sp.simplify(parse_latex(init_value.split("=")[0]))
    ac = sp.sstr(equation.coeff(x, 2) * equation.coeff(x, 0))
    answer = re.compile(ac)
    hint = ac
    value = tuple([(answer, hint)])
    return value

def factor_1_b(init_value):
    x = symbols('x')
    equation = sp.simplify(parse_latex(init_value.split("=")[0]))
    sum_b = equation.coeff(x, 1)
    product_ac = equation.coeff(x, 2) * equation.coeff(x, 0)

    factors = [f for factor in sp.divisors(int(product_ac)) for f in (factor, -factor)]
    factorlist = [(abs((int(product_ac)/f+f)-int(sum_b)), f) for f in factors]
    factorlist.sort()
    value = tuple([(re.compile(str(f)), str(f)) for _, f in factorlist])
    return value


def factor_2_b(init_value, f1):
    x = symbols('x')
    equation = sp.simplify(parse_latex(init_value.split("=")[0]))
    product_ac = equation.coeff(x, 2) * equation.coeff(x, 0)
    answer = re.compile(str(int(int(product_ac)/int(f1))))
    hint = str(int(int(product_ac)/int(f1)))
    value = tuple([(answer, hint)])
    return value

def sum_factor(f1, f2):
    sum_factor = int(f1) + int(f2)
    value = tuple([(re.compile(str(sum_factor)), str(sum_factor))])
    return value

def sum_c(init_value, sum_factor):
    x = symbols('x')
    equation = sp.simplify(parse_latex(init_value.split("=")[0]))
    sum_b = equation.coeff(x, 1)
    if sum_b == int(sum_factor):
        value = tuple([(re.compile(re.sub(r'([-+^()*])', r'\\\1', sstr(parse_latex('checked')))), 'checked')])
    else:
        value = tuple([(re.compile(re.sub(r'([-+^()*])', r'\\\1', sstr(parse_latex('unchecked')))), 'unchecked')])
    return value


def expanded_equation(init_value, f1, f2):
    facts = list()
    x = symbols('x')
    equation = sp.simplify(parse_latex(init_value).lhs)
    a, c = equation.coeff(x, 2), equation.coeff(x, 0)
    for p in [(f1, f2), (f2, f1)]:
        factored = f"{a*x}^{2}+{p[0]}x+{p[1]}x+{c}=0".replace("+-", "-").replace("*", "")
        answer = re.compile(re.sub(r'([-+()*])', r'\\\1', sp.sstr(parse_latex(factored), order='grlex')))
        hint = factored
        facts.append((answer, hint))
    return tuple(facts)


Domain = {
    'done': Operator(head=('done', V('kc')),
                     precondition=[Fact(start=True)],
                     effects=[Fact(field='done', value=((re.compile('x'),),), kc=V('kc'), answer=True)],
    ),

    'b_value': Operator(head=('b_value', V('equation'), V('kc')),
                        precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                        effects=[Fact(field='b_value', value=(b_value, V('eq')), kc=V('kc'), answer=True)],
    ),

    'ac_value': Operator(head=('ac_value', V('equation'), V('kc')),
                         precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                         effects=[Fact(field='ac_value', value=(ac_value, V('eq')), kc=V('kc'), answer=True)],
    ),

    'factor_1_b': Operator(head=('factor_1_b', V('equation'), V('kc')),
                           precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                           effects=[Fact(field='factor_1_b', value=(factor_1_b, V('eq')), kc=V('kc'), answer=True)],
    ),

    'factor_2_b': Operator(head=('factor_2_b', V('equation'), V('f1'), V('kc')),
                           precondition=Fact(field=V('equation'), value=V('eq'), answer=False)&
                                         Fact(field=V('f1'), value=V('f1eq'), kc=V('f1kc'), answer=True),
                           effects=[Fact(field='factor_2_b', value=(factor_2_b, V('eq'), V('f1eq')), kc=V('kc'), answer=True)],
    ),

    'sum_factor': Operator(head=('sum_factor', V('f1'), V('f2'), V('kc')),
                            precondition=Fact(field=V('f1'), value=V('f1eq'), kc=V('f1kc'), answer=True)&
                                         Fact(field=V('f2'), value=V('f2eq'), kc=V('f2kc'), answer=True),
                            effects=[Fact(field='sum_factor', value=(sum_factor, V('f1eq'), V('f2eq')), kc=V('kc'), answer=True)],
    ),

    'sum_c': Operator(head=('sum_c', V('equation'), V('sum_factor'), V('kc')),
                        precondition=Fact(field=V('equation'), value=V('eq'), answer=False)&
                                     Fact(field=V('sum_factor'), value=V('sum_factor_eq'), kc=V('sum_factor_kc'), answer=True),
                        effects=[Fact(field='sum_c', value=(sum_c, V('eq'), V('sum_factor_eq')), kc=V('kc'), answer=True)],
    ),

    'expanded_equation': Operator(head=('expanded_equation', V('equation'), V('f1'), V('f2'), V('kc')),
                                precondition=Fact(field=V('equation'), value=V('eq'), answer=False)&
                                             Fact(field=V('f1'), value=V('f1eq'), kc=V('f1kc'), answer=True)&
                                             Fact(field=V('f2'), value=V('f2eq'), kc=V('f2kc'), answer=True),
                                effects=[Fact(field='expanded_equation', value=(expanded_equation, V('eq'), V('f1eq'), V('f2eq')), kc=V('kc'), answer=True)],
    ),
    
    'solve': Method(head=('solve', V('equation')),
                    preconditions=[
                        Fact(scaffold='level_1'),
                        Fact(scaffold='level_0'),
                    ],
                    subtasks=[

                        [
                            Task(head=('b_value', V('equation'), ('b_value',)), primitive=True),
                            Task(head=('ac_value', V('equation'), ('ac_value',)), primitive=True),
                            Task(head=('factor_1_b', V('equation'), ('factor_1_b',)), primitive=True),
                            Task(head=('factor_2_b', V('equation'), 'factor_1_b', ('factor_2_b',)), primitive=True),
                            Task(head=('sum_factor', 'factor_1_b', 'factor_2_b', ('sum_factor',)), primitive=True),
                            Task(head=('sum_c', V('equation'), 'sum_factor', ('sum_c',)), primitive=True),
                            Task(head=('expanded_equation', V('equation'), 'factor_1_b', 'factor_2_b', ('expanded_equation',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [
                            Task(head=('factor_1_b', V('equation'), ('factor_1_b',)), primitive=True),
                            Task(head=('factor_2_b', V('equation'), 'factor_1_b', ('factor_2_b',)), primitive=True),
                            Task(head=('sum_factor', 'factor_1_b', 'factor_2_b', ('sum_factor',)), primitive=True),
                            Task(head=('sum_c', V('equation'), 'sum_factor', ('sum_c',)), primitive=True),
                            Task(head=('expanded_equation', V('equation'), 'factor_1_b', 'factor_2_b', ('expanded_equation',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],
                    ]
    ),
}

def htn_quadratic_equations_factorize_kc_mapping():
    kcs = {
        "b_value": "b_value",
        "ac_value": "ac_value",
        'factor_1_b': "factor_1_b",
        'factor_2_b': "factor_2_b",
        'sum_factor': "sum_factor",
        'sum_c': "sum_c",
        'expanded_equation': "expanded_equation",
        'done': "done",
    }
    return kcs


def htn_quadratic_equations_factorize_intermediate_hints():

    hints = {
        "b_value": ["Here \(b\) is coefficient of \(x\)."],
        "ac_value": ["Here \(ac\) is the product of the coefficients of \(x^2\) and constant."],
        'factor_1_b': ["Enter a factor of \(ac\)."],
        'factor_2_b': ["Enter the other factor of \(ac\)."],
        'sum_factor': ["Add the two factos to get the sum."],
        'sum_c': ["Check this box if the sum of the factors is equal to \(b\)."],
        'expanded_equation': ["Expand the \(x\) term using the factors"],
    }
    return hints
def htn_quadratic_equations_factorize_studymaterial():
    study_material = studymaterial["quadratic_equations_factorize"]
    return study_material

htn_loaded_models.register(HTNCognitiveModel('htn_quadratic_equations',
                                             'htn_quadratic_equations_factorize',
                                             Domain,
                                             Task(head=('solve', 'equation'), primitive=False),
                                             htn_quadratic_equations_factorize_problem,
                                             htn_quadratic_equations_factorize_kc_mapping(),
                                             htn_quadratic_equations_factorize_intermediate_hints(),
                                             htn_quadratic_equations_factorize_studymaterial()))