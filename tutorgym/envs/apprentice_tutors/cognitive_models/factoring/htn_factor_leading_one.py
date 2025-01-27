import sympy as sp
from random import randint, choice

import sympy as sp
from sympy import sstr, latex, symbols, Eq, solve
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
import math
from random import random
from functools import reduce


def quadratic_factorization(expression):
    x = sp.symbols('x')
    expression = expression.replace("^", "**")  # Replace "^" with "**" for exponentiation
    expression = re.sub(r'(\d+)([a-zA-Z])', r'\1*\2', expression)  # Add "*" for multiplication between coefficient and variable
    factored_expression = sp.factor(expression)

    return str(factored_expression.args[0]).replace("*",""), str(factored_expression.args[1]).replace("*","")

def factors(n):
    fset = set(reduce(list.__add__,
               ([i, n//i] for i in range(1, int(abs(n)**0.5) + 1)
                if n % i == 0)))

    other_signs = set([-1 * f for f in fset])
    fset = fset.union(other_signs)

    return fset

def htn_factor_leading_one_problem():
    n1 = 1

    print(type(random))

    n2 = randint(1, 5)
    if random() > 0.5:
        n2 *= -1

    n3 = 1

    n4 = randint(1, 5)
    if random() > 0.5:
        n4 *= -1

    problem = "x^2"

    b_value = n1*n4+n2*n3
    if b_value == 0:
        return htn_factor_leading_one_problem()

    if b_value > 0:
        problem += "+"

    problem += "{}x".format(b_value)

    c_value = n2 * n4
    if c_value > 0:
        problem += "+"

    problem += "{}".format(c_value)

    return problem

def a_value(init_value):
    x = symbols('x')
    equation = sp.simplify(parse_latex(init_value.split("=")[0]))
    answer = str(equation.coeff(x, 2))
    return tuple([(re.compile(answer), answer)])

def b_value(init_value):
    x = symbols('x')
    equation = sp.simplify(parse_latex(init_value.split("=")[0]))
    answer = str(equation.coeff(x, 1))
    return tuple([(re.compile(answer), answer)])

def c_value(init_value):
    x = symbols('x')
    equation = sp.simplify(parse_latex(init_value.split("=")[0]))
    answer = str(equation.coeff(x, 0))
    return tuple([(re.compile(answer), answer)])

def ac_value(init_value):
    x = symbols('x')
    equation = sp.simplify(parse_latex(init_value.split("=")[0]))
    answer = str(equation.coeff(x, 0) * equation.coeff(x, 2))
    return tuple([(re.compile(answer), answer)])

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

def first_expression(init_value):
    facts = list()
    init_value = parse_latex(init_value)
    factors = sp.factor(init_value).args
    if factors[1] == 2:
        answer = re.compile(re.sub(r'([-+()*])', r'\\\1', sp.sstr(factors[0], order="grlex")))    
        hint = latex(factors[0])
        facts.append((answer, hint))
    else:
        for factor in factors:
            answer = re.compile(re.sub(r'([-+()*])', r'\\\1', sp.sstr(factor, order="grlex")))    
            hint = latex(factor)
            facts.append((answer, hint))
    return tuple(facts)

def second_expression(init_value, first_expression):
    init_value = sp.factor(parse_latex(init_value))
    first_expression = parse_latex(first_expression)
    equation = sp.div(init_value, first_expression)[0]
    hint = latex(equation)
    answer = re.compile(re.sub(r'([-+()*])', r'\\\1', sp.sstr(equation, order="grlex")))
    value = tuple([(answer, hint)])
    return value

def final_answer(init_value):
    equation = parse_latex(init_value)
    factor = sp.factor(equation)
    hint = latex(factor)
    answer = re.compile(re.sub(r'([-+()*])', r'\\\1', sp.sstr(factor, order="grlex")))
    value = tuple([(answer, hint)])
    return value

Domain = {
    'done': Operator(head=('done', V('kc')),
                     precondition=[Fact(start=True)],
                     effects=[Fact(field='done', value=((re.compile('x'),),), kc=V('kc'), answer=True)],
    ),

    'b_value': Operator(head=('b_value', V('equation'), V('kc')),
                        precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                        effects=[Fact(field='b_value', value=(b_value, V('eq')), kc=V('kc'), answer=True)],
    ),

    'c_value': Operator(head=('c_value', V('equation'), V('kc')),
                        precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                        effects=[Fact(field='c_value', value=(c_value, V('eq')), kc=V('kc'), answer=True)],
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

    'first_expression': Operator(head=('first_expression', V('equation'), V('kc')),
                                    precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                                    effects=[Fact(field='first_expression', value=(first_expression, V('eq')), kc=V('kc'), answer=True)],
    ),

    'second_expression': Operator(head=('second_expression', V('equation'), V('first_expression'), V('kc')),
                                    precondition=Fact(field=V('equation'), value=V('eq'), answer=False)&
                                                 Fact(field=V('first_expression'), value=V('feq'), kc=V('fkc'), answer=True),
                                    effects=[Fact(field='second_expression', value=(second_expression, V('eq'), V('feq')), kc=V('kc'), answer=True)],  
    ),

    'final_answer': Operator(head=('final_answer', V('equation'), V('kc')),
                            precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                            effects=[Fact(field='final_answer', value=(final_answer, V('eq')), kc=V('kc'), answer=True)],
    ),

    'solve': Method(head=('solve', V('equation')),
                    preconditions=[
                        Fact(scaffold='level_2'),
                        Fact(scaffold='level_1'),
                        Fact(scaffold='level_0'),
                    ],
                    subtasks=[

                        [   
                            Task(head=('b_value', V('equation'), ('b_value',)), primitive=True),
                            Task(head=('c_value', V('equation'), ('c_value',)), primitive=True),
                            Task(head=('factor_1_b', V('equation'), ('factor_1_b',)), primitive=True),
                            Task(head=('factor_2_b', V('equation'), 'factor_1_b', ('factor_2_b',)), primitive=True),
                            Task(head=('sum_factor', 'factor_1_b', 'factor_2_b', ('sum_factor',)), primitive=True),
                            Task(head=('sum_c', V('equation'), 'sum_factor', ('sum_c',)), primitive=True),
                            Task(head=('first_expression', V('equation'), ('first_expression',)), primitive=True),
                            Task(head=('second_expression', V('equation'), 'first_expression', ('second_expression',)), primitive=True),
                            Task(head=('final_answer', V('equation'), ('final_answer',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [   
                            Task(head=('factor_1_b', V('equation'), ('factor_1_b',)), primitive=True),
                            Task(head=('factor_2_b', V('equation'), 'factor_1_b', ('factor_2_b',)), primitive=True),
                            Task(head=('sum_factor', 'factor_1_b', 'factor_2_b', ('sum_factor',)), primitive=True),
                            Task(head=('sum_c', V('equation'), 'sum_factor', ('sum_c',)), primitive=True),
                            Task(head=('first_expression', V('equation'), ('first_expression',)), primitive=True),
                            Task(head=('second_expression', V('equation'), 'first_expression', ('second_expression',)), primitive=True),
                            Task(head=('final_answer', V('equation'), ('final_answer',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [   
                            Task(head=('first_expression', V('equation'), ('first_expression',)), primitive=True),
                            Task(head=('second_expression', V('equation'), 'first_expression', ('second_expression',)), primitive=True),
                            Task(head=('final_answer', V('equation'), ('final_answer',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],
                    ]
    ),
}

def htn_factor_leading_one_kc_mapping():
    kcs = {
        'b_value':'b_value',
        'c_value':'c_value',
        'factor_1_b':'factor_1_b',
        'factor_2_b':'factor_2_b',
        'sum_factor':'sum_factor',
        'sum_c':'sum_c',
        'first_expression':'first_expression',
        'second_expression':'second_expression',
        'final_answer':'final_answer',
        'done':'done',
    }
    return kcs




def htn_factor_leading_one_intermediate_hints():
    hints = {
        "b_value": [
            "The b value is extracted from the middle term of the trinomial."],
        "c_value": [
            "The c value is extracted from the last term of the trinomial."],
        'factor_1_b': ["Enter a factor of ac."],
        'factor_2_b': ["Enter the value that when multipled with"
                                  " the other factor yields ac."],
        'sum_factor': [
            "This value is computed by adding the two factors in this row."],
        'sum_c': [
            "Check this box if the sum of the factors is equal to b."],
        'first_expression': [
            "This is the first factor of the trinomial."],
        'second_expression': [
            "This is the second factor of the trinomial."],
        'final_answer': ["Enter the factored form of the trinomial."],
    }
    return hints

def htn_factor_leading_one_studymaterial():
    study_material = studymaterial["factor_leading_one"]
    return study_material

htn_loaded_models.register(HTNCognitiveModel('htn_factoring_polynomials',    
                                             'htn_factor_leading_one',
                                             Domain,
                                             Task(head=('solve', 'equation'), primitive=False),
                                             htn_factor_leading_one_problem,
                                             htn_factor_leading_one_kc_mapping(),
                                             htn_factor_leading_one_intermediate_hints(),
                                             htn_factor_leading_one_studymaterial()))