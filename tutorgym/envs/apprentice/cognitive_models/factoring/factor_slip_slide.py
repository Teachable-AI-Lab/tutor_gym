import sympy as sp
from random import randint

import sympy as sp
from sympy import sstr, latex, symbols 
from sympy.parsing.latex._parse_latex_antlr import parse_latex
import re

from random import randint
from shop2.domain import Task, Operator, Method
from shop2.fact import Fact
from shop2.conditions import Filter
from shop2.common import V

import math
from random import random
from functools import reduce


def quadratic_factorization(expression):
    x = sp.symbols('x')

    # Convert the expression to SymPy format
    expression = expression.replace("^", "**")  # Replace "^" with "**" for exponentiation
    expression = re.sub(r'(\d+)([a-zA-Z])', r'\1*\2', expression)  # Add "*" for multiplication between coefficient and variable

    # Parse the expression and factor it
    factored_expression = sp.factor(expression)

    return str(factored_expression.args[0]).replace("*",""), str(factored_expression.args[1]).replace("*","")

def factors(n):
    fset = set(
        reduce(list.__add__,
               ([i, n // i]
                for i in range(1,
                               int(abs(n)**0.5) + 1) if n % i == 0)))

    other_signs = set([-1 * f for f in fset])
    fset = fset.union(other_signs)

    return fset


def factor_slip_slide_problem():
    n1 = randint(2, 5)
    # if random() > 0.5:
    #     n1 *= -1

    n2 = randint(1, 5)
    if random() > 0.5:
        n2 *= -1

    n3 = randint(1, 5)
    # if random() > 0.5:
    #     n3 *= -1

    n4 = randint(1, 5)
    if random() > 0.5:
        n4 *= -1

    if math.gcd(n1, n2) != 1 or math.gcd(n3, n4) != 1:
        return factor_slip_slide_problem()

    problem = "{}x^2".format(n1 * n3)

    b_value = n1 * n4 + n2 * n3
    if b_value == 0:
        return factor_slip_slide_problem()

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

def new_equation(init_value):
    x = symbols('x')
    equation = sp.simplify(parse_latex(init_value.split("=")[0]))
    a, b, c = equation.coeff(x, 2), equation.coeff(x, 1), equation.coeff(x, 0)
    ac = a * c
    equation = x**2 + b*x + ac
    hint = latex(equation)
    if b > 0:
        if ac > 0:
            equation = f"(x**2 + {b}*x) + {ac}"
        else:
            equation = f"(x**2 + {b}*x) - {abs(ac)}"
    else:
        if ac > 0:
            equation = f"(x**2 - {abs(b)}*x) + {ac}"
        else:
            equation = f"(x**2 - {abs(b)}*x) - {abs(ac)}"

    answer = re.compile(re.sub(r'([-+()*])', r'\\\1', equation.replace("- 1*", "- ").replace("+ 1*", "+ ")))
    value = tuple([(answer, hint)])
    return value

def new_b_value(new_equation):
    x = symbols('x')
    equation = sp.simplify(parse_latex(new_equation.split("=")[0]))
    answer = str(equation.coeff(x, 1))
    return tuple([(re.compile(answer), answer)])

def new_c_value(new_equation):
    x = symbols('x')
    equation = sp.simplify(parse_latex(new_equation.split("=")[0]))
    answer = str(equation.coeff(x, 0))
    return tuple([(re.compile(answer), answer)])
            
def factor_1_b(new_equation):
    x = symbols('x')
    equation = sp.simplify(parse_latex(new_equation.split("=")[0]))
    sum_b = equation.coeff(x, 1)
    product_ac = equation.coeff(x, 2) * equation.coeff(x, 0)
    factors = [f for factor in sp.divisors(int(product_ac)) for f in (factor, -factor)]
    factorlist = [(abs((int(product_ac)/f+f)-int(sum_b)), f) for f in factors]
    factorlist.sort()
    value = tuple([(re.compile(str(f)), str(f)) for _, f in factorlist])
    return value

def factor_2_b(new_equation, f1):
    x = symbols('x')
    equation = sp.simplify(parse_latex(new_equation.split("=")[0]))
    product_ac = equation.coeff(x, 2) * equation.coeff(x, 0)
    answer = re.compile(str(int(int(product_ac)/int(f1))))
    hint = str(int(int(product_ac)/int(f1)))
    value = tuple([(answer, hint)])
    return value

def sum_factor(f1, f2):
    sum_factor = int(f1) + int(f2)
    value = tuple([(re.compile(str(sum_factor)), str(sum_factor))])
    return value

def sum_c(new_equation, sum_factor):
    x = symbols('x')
    equation = sp.simplify(parse_latex(new_equation.split("=")[0]))
    sum_b = equation.coeff(x, 1)
    if sum_b == int(sum_factor):
        value = tuple([(re.compile(re.sub(r'([-+^()*])', r'\\\1', sstr(parse_latex('checked')))), 'checked')])
    else:
        value = tuple([(re.compile(re.sub(r'([-+^()*])', r'\\\1', sstr(parse_latex('unchecked')))), 'unchecked')])
    return value

def new_first_expression(factor_1_b, factor_2_b):
    x = symbols('x')
    equation_1 = x + int(factor_1_b)
    hint_1 = latex(equation_1)
    answer_1 = re.compile(re.sub(r'([-+()*])', r'\\\1', sp.sstr(equation_1, order="grlex")))

    equation_2 = x + int(factor_2_b)
    hint_2 = latex(equation_2)
    answer_2 = re.compile(re.sub(r'([-+()*])', r'\\\1', sp.sstr(equation_2, order="grlex")))

    return tuple([
        (answer_1, hint_1),
        (answer_2, hint_2)
    ])

def new_second_expression(new_first_expression, factor_1_b, factor_2_b):
    x = symbols('x')
    new_first_expression = parse_latex(new_first_expression)
    factor_1_b = int(factor_1_b)
    factor_2_b = int(factor_2_b)
    coeff = new_first_expression.coeff(x, 0)
    if coeff == factor_1_b:
        c = factor_2_b
    else:
        c = factor_1_b
    equation = x + c
    hint = latex(equation)
    answer = re.compile(re.sub(r'([-+()*])', r'\\\1', sp.sstr(equation, order="grlex")))
    value = tuple([(answer, hint)])
    return value

def raw_first_expression(a_value, new_first_expression):
    x = symbols('x')
    c_value = parse_latex(new_first_expression).coeff(x, 0)
    a_value = int(a_value)
    if a_value*c_value < 0:
        equation = f"x - {abs(c_value)}/{abs(a_value)}"
        hint = "x - \\frac{" + str(abs(c_value)) + "}{" + str(abs(a_value)) + "}"
    else:
        equation = f"x + {abs(c_value)}/{abs(a_value)}"
        hint = "x + \\frac{" + str(abs(c_value)) + "}{" + str(abs(a_value)) + "}"
    answer = re.compile(re.sub(r'([-+()*])', r'\\\1', equation))
    value = tuple([(answer, hint)])
    return value

def raw_second_expression(a_value, new_second_expression):
    x = symbols('x')
    c_value = parse_latex(new_second_expression).coeff(x, 0)
    a_value = int(a_value)
    if a_value*c_value < 0:
        equation = f"x - {abs(c_value)}/{abs(a_value)}"
        hint = "x - \\frac{" + str(abs(c_value)) + "}{" + str(abs(a_value)) + "}"
    else:
        equation = f"x + {abs(c_value)}/{abs(a_value)}"
        hint = "x + \\frac{" + str(abs(c_value)) + "}{" + str(abs(a_value)) + "}"
    answer = re.compile(re.sub(r'([-+()*])', r'\\\1', equation))
    value = tuple([(answer, hint)])
    return value

def simplified_first_expression(a_value, raw_first_expression):
    x = symbols('x')
    c_value = parse_latex(raw_first_expression).coeff(x, 0)
    a_value = int(a_value)
    multiplier = sp.gcd(c_value, a_value)
    a_value /= multiplier
    c_value /= multiplier
    if a_value*c_value < 0:
        equation = f"x - {abs(c_value)}/{abs(a_value)}"
        hint = "x - \\frac{" + str(abs(c_value)) + "}{" + str(abs(a_value)) + "}"
    else:
        equation = f"x + {abs(c_value)}/{abs(a_value)}"
        hint = "x + \\frac{" + str(abs(c_value)) + "}{" + str(abs(a_value)) + "}"
    answer = re.compile(re.sub(r'([-+()*])', r'\\\1', equation))
    value = tuple([(answer, hint)])
    equation = x + sp.Mul(c_value, 1/a_value)
    hint = latex(equation)
    answer = re.compile(re.sub(r'([-+()*])', r'\\\1', sp.sstr(equation, order="grlex")))
    value = tuple([(answer, hint)])
    return value

def simplified_second_expression(a_value, raw_second_expression):
    x = symbols('x')
    c_value = parse_latex(raw_second_expression).coeff(x, 0)
    a_value = int(a_value)
    multiplier = sp.gcd(c_value, a_value)
    a_value /= multiplier
    c_value /= multiplier
    if a_value*c_value < 0:
        equation = f"x - {abs(c_value)}/{abs(a_value)}"
        hint = "x - \\frac{" + str(abs(c_value)) + "}{" + str(abs(a_value)) + "}"
    else:
        equation = f"x + {abs(c_value)}/{abs(a_value)}"
        hint = "x + \\frac{" + str(abs(c_value)) + "}{" + str(abs(a_value)) + "}"
    answer = re.compile(re.sub(r'([-+()*])', r'\\\1', equation))
    value = tuple([(answer, hint)])
    equation = x + sp.Mul(c_value, 1/a_value)
    hint = latex(equation)
    answer = re.compile(re.sub(r'([-+()*])', r'\\\1', sp.sstr(equation, order="grlex")))
    value = tuple([(answer, hint)])
    return value

def final_first_expression(init_value):
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

def final_second_expression(init_value, final_first_expression):
    init_value = sp.factor(parse_latex(init_value))
    final_first_expression = parse_latex(final_first_expression)
    equation = sp.div(init_value, final_first_expression)[0]
    hint = latex(equation)
    answer = re.compile(re.sub(r'([-+()*])', r'\\\1', sp.sstr(equation, order="grlex")))
    value = tuple([(answer, hint)])
    return value

def final_answer(new_equation):
    equation = parse_latex(new_equation)
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

    'a_value': Operator(head=('a_value', V('equation'), V('kc')),
                        precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                        effects=[Fact(field='a_value', value=(a_value, V('eq')), kc=V('kc'), answer=True)],
    ),

    'b_value': Operator(head=('b_value', V('equation'), V('kc')),
                        precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                        effects=[Fact(field='b_value', value=(b_value, V('eq')), kc=V('kc'), answer=True)],
    ),

    'c_value': Operator(head=('c_value', V('equation'), V('kc')),
                        precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                        effects=[Fact(field='c_value', value=(c_value, V('eq')), kc=V('kc'), answer=True)],
    ),

    'ac_value': Operator(head=('ac_value', V('equation'), V('kc')),
                        precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                        effects=[Fact(field='ac_value', value=(ac_value, V('eq')), kc=V('kc'), answer=True)],
    ),

    'new_equation': Operator(head=('new_equation', V('equation'), V('kc')),
                            precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                            effects=[Fact(field='new_equation', value=(new_equation, V('eq')), kc=V('kc'), answer=True)],
    ),

    'new_b_value': Operator(head=('new_b_value', V('new_equation'), V('kc')),
                            precondition=Fact(field=V('new_equation'), value=V('eq'), kc=V('neq'), answer=True),
                            effects=[Fact(field='new_b_value', value=(new_b_value, V('eq')), kc=V('kc'), answer=True)],
    ),

    'new_c_value': Operator(head=('new_c_value', V('new_equation'), V('kc')),
                            precondition=Fact(field=V('new_equation'), value=V('eq'), kc=V('neq'), answer=True),
                            effects=[Fact(field='new_c_value', value=(new_c_value, V('eq')), kc=V('kc'), answer=True)],
    ),

    'factor_1_b': Operator(head=('factor_1_b', V('new_equation'), V('kc')),
                           precondition=Fact(field=V('new_equation'), value=V('neq'), kc=V('kneq'), answer=True),
                           effects=[Fact(field='factor_1_b', value=(factor_1_b, V('neq')), kc=V('kc'), answer=True)],
    ),

    'factor_2_b': Operator(head=('factor_2_b', V('new_equation'), V('f1'), V('kc')),
                           precondition=Fact(field=V('new_equation'), value=V('neq'), kc=V('kneq'), answer=True)&
                                         Fact(field=V('f1'), value=V('f1eq'), kc=V('f1kc'), answer=True),
                           effects=[Fact(field='factor_2_b', value=(factor_2_b, V('neq'), V('f1eq')), kc=V('kc'), answer=True)],
    ),

    'sum_factor': Operator(head=('sum_factor', V('f1'), V('f2'), V('kc')),
                            precondition=Fact(field=V('f1'), value=V('f1eq'), kc=V('f1kc'), answer=True)&
                                         Fact(field=V('f2'), value=V('f2eq'), kc=V('f2kc'), answer=True),
                            effects=[Fact(field='sum_factor', value=(sum_factor, V('f1eq'), V('f2eq')), kc=V('kc'), answer=True)],
    ),

    'sum_c': Operator(head=('sum_c', V('new_equation'), V('sum_factor'), V('kc')),
                        precondition=Fact(field=V('new_equation'), value=V('neq'), kc=V('kneq'), answer=True)&
                                     Fact(field=V('sum_factor'), value=V('sum_factor_eq'), kc=V('sum_factor_kc'), answer=True),
                        effects=[Fact(field='sum_c', value=(sum_c, V('neq'), V('sum_factor_eq')), kc=V('kc'), answer=True)],
    ),

    'new_first_expression': Operator(head=('new_first_expression', V('factor_1_b'), V('factor_2_b'), V('kc')),
                                    precondition=Fact(field=V('factor_1_b'), value=V('feq'), kc=V('fkc'), answer=True)&
                                                    Fact(field=V('factor_2_b'), value=V('f2eq'), kc=V('f2kc'), answer=True),
                                    effects=[Fact(field='new_first_expression', value=(new_first_expression, V('feq'), V('f2eq')), kc=V('kc'), answer=True)],   
    ),

    'new_second_expression': Operator(head=('new_second_expression', V('new_first_expression'), V('factor_1_b'), V('factor_2_b'), V('kc')),
                                    precondition=Fact(field=V('new_first_expression'), value=V('feq'), kc=V('fkc'), answer=True)&
                                                    Fact(field=V('factor_1_b'), value=V('f1eq'), kc=V('f1kc'), answer=True)&
                                                    Fact(field=V('factor_2_b'), value=V('f2eq'), kc=V('f2kc'), answer=True),
                                    effects=[Fact(field='new_second_expression', value=(new_second_expression, V('feq'), V('f1eq'), V('f2eq')), kc=V('kc'), answer=True)],
    ),

    'raw_first_expression': Operator(head=('raw_first_expression', V('a_value'), V('new_first_expression'), V('kc')),
                                    precondition=Fact(field=V('new_first_expression'), value=V('neq'), kc=V('nkeq'), answer=True)&
                                                    Fact(field=V('a_value'), value=V('aeq'), kc=V('akc'), answer=True),
                                    effects=[Fact(field='raw_first_expression', value=(raw_first_expression, V('aeq'), V('neq')), kc=V('kc'), answer=True)],
    ),

    'raw_second_expression': Operator(head=('raw_second_expression', V('a_value'), V('new_second_expression'), V('kc')),
                                    precondition=Fact(field=V('new_second_expression'), value=V('neq'), kc=V('nkeq'), answer=True)&
                                                    Fact(field=V('a_value'), value=V('aeq'), kc=V('akc'), answer=True),
                                    effects=[Fact(field='raw_second_expression', value=(raw_second_expression, V('aeq'), V('neq')), kc=V('kc'), answer=True)],
    ),

    'simplified_first_expression': Operator(head=('simplified_first_expression', V('a_value'), V('raw_first_expression'), V('kc')),
                                    precondition=Fact(field=V('a_value'), value=V('aeq'), kc=V('akc'), answer=True)&
                                                    Fact(field=V('raw_first_expression'), value=V('feq'), kc=V('fkc'), answer=True),
                                    effects=[Fact(field='simplified_first_expression', value=(simplified_first_expression, V('aeq'), V('feq')), kc=V('kc'), answer=True)],
    ),

    'simplified_second_expression': Operator(head=('simplified_second_expression', V('a_value'), V('raw_second_expression'), V('kc')),
                                    precondition=Fact(field=V('a_value'), value=V('aeq'), kc=V('akc'), answer=True)&
                                                    Fact(field=V('raw_second_expression'), value=V('feq'), kc=V('fkc'), answer=True),
                                    effects=[Fact(field='simplified_second_expression', value=(simplified_second_expression, V('aeq'), V('feq')), kc=V('kc'), answer=True)],
    ),

    'final_first_expression': Operator(head=('final_first_expression', V('equation'), V('kc')),
                                    precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                                    effects=[Fact(field='final_first_expression', value=(final_first_expression, V('eq')), kc=V('kc'), answer=True)],
    ),

    'final_second_expression': Operator(head=('final_second_expression', V('equation'), V('final_first_expression'), V('kc')),
                                    precondition=Fact(field=V('equation'), value=V('eq'), answer=False)&
                                                 Fact(field=V('final_first_expression'), value=V('feq'), kc=V('fkc'), answer=True),
                                    effects=[Fact(field='final_second_expression', value=(final_second_expression, V('eq'), V('feq')), kc=V('kc'), answer=True)],  
    ),

    'final_answer': Operator(head=('final_answer', V('equation'), V('kc')),
                            precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                            effects=[Fact(field='final_answer', value=(final_answer, V('eq')), kc=V('kc'), answer=True)],
    ),

    'solve': Method(head=('solve', V('equation')),
                    preconditions=[
                        Fact(scaffold='level_6'),
                        Fact(scaffold='level_5'),
                        Fact(scaffold='level_4'),
                        Fact(scaffold='level_3'),
                        Fact(scaffold='level_2'),
                        Fact(scaffold='level_1'),
                        Fact(scaffold='level_0'),
                    ],
                    subtasks=[

                        [   
                            Task(head=('a_value', V('equation'), ('a_value',)), primitive=True), 
                            Task(head=('b_value', V('equation'), ('b_value',)), primitive=True),
                            Task(head=('c_value', V('equation'), ('c_value',)), primitive=True),
                            Task(head=('ac_value', V('equation'), ('ac_value',)), primitive=True),
                            Task(head=('new_equation', V('equation'), ('new_equation',)), primitive=True),
                            Task(head=('new_b_value', 'new_equation', ('new_b_value',)), primitive=True),
                            Task(head=('new_c_value', 'new_equation', ('new_c_value',)), primitive=True),
                            Task(head=('factor_1_b', 'new_equation', ('factor_1_b',)), primitive=True),
                            Task(head=('factor_2_b', 'new_equation', 'factor_1_b', ('factor_2_b',)), primitive=True),
                            Task(head=('sum_factor', 'factor_1_b', 'factor_2_b', ('sum_factor',)), primitive=True),
                            Task(head=('sum_c', 'new_equation', 'sum_factor', ('sum_c',)), primitive=True),
                            Task(head=('new_first_expression', 'factor_1_b', 'factor_2_b', ('new_first_expression',)), primitive=True),
                            Task(head=('new_second_expression', 'new_first_expression', 'factor_1_b', 'factor_2_b', ('new_second_expression',)), primitive=True),
                            Task(head=('raw_first_expression', 'a_value', 'new_first_expression', ('raw_first_expression',)), primitive=True),
                            Task(head=('raw_second_expression', 'a_value', 'new_second_expression', ('raw_second_expression',)), primitive=True),
                            Task(head=('simplified_first_expression', 'a_value', 'new_first_expression', ('simplified_first_expression',)), primitive=True),
                            Task(head=('simplified_second_expression', 'a_value', 'new_second_expression', ('simplified_second_expression',)), primitive=True),
                            Task(head=('final_first_expression', V('equation'), ('final_first_expression',)), primitive=True),
                            Task(head=('final_second_expression', V('equation'), 'final_first_expression', ('final_second_expression',)), primitive=True),
                            Task(head=('final_answer', V('equation'), ('final_answer',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [   
                            Task(head=('a_value', V('equation'), ('a_value',)), primitive=True), 
                            Task(head=('b_value', V('equation'), ('b_value',)), primitive=True),
                            Task(head=('c_value', V('equation'), ('c_value',)), primitive=True),
                            Task(head=('ac_value', V('equation'), ('ac_value',)), primitive=True),
                            Task(head=('new_equation', V('equation'), ('new_equation',)), primitive=True),
                            Task(head=('new_b_value', 'new_equation', ('new_b_value',)), primitive=True),
                            Task(head=('new_c_value', 'new_equation', ('new_c_value',)), primitive=True),
                            Task(head=('factor_1_b', 'new_equation', ('factor_1_b',)), primitive=True),
                            Task(head=('factor_2_b', 'new_equation', 'factor_1_b', ('factor_2_b',)), primitive=True),
                            Task(head=('sum_factor', 'factor_1_b', 'factor_2_b', ('sum_factor',)), primitive=True),
                            Task(head=('sum_c', 'new_equation', 'sum_factor', ('sum_c',)), primitive=True),
                            Task(head=('new_first_expression', 'factor_1_b', 'factor_2_b', ('new_first_expression',)), primitive=True),
                            Task(head=('new_second_expression', 'new_first_expression', 'factor_1_b', 'factor_2_b', ('new_second_expression',)), primitive=True),
                            Task(head=('raw_first_expression', 'a_value', 'new_first_expression', ('raw_first_expression',)), primitive=True),
                            Task(head=('raw_second_expression', 'a_value', 'new_second_expression', ('raw_second_expression',)), primitive=True),
                            Task(head=('final_first_expression', V('equation'), ('final_first_expression',)), primitive=True),
                            Task(head=('final_second_expression', V('equation'), 'final_first_expression', ('final_second_expression',)), primitive=True),
                            Task(head=('final_answer', V('equation'), ('final_answer',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [   
                            Task(head=('a_value', V('equation'), ('a_value',)), primitive=True), 
                            Task(head=('b_value', V('equation'), ('b_value',)), primitive=True),
                            Task(head=('c_value', V('equation'), ('c_value',)), primitive=True),
                            Task(head=('ac_value', V('equation'), ('ac_value',)), primitive=True),
                            Task(head=('new_equation', V('equation'), ('new_equation',)), primitive=True),
                            Task(head=('new_b_value', 'new_equation', ('new_b_value',)), primitive=True),
                            Task(head=('new_c_value', 'new_equation', ('new_c_value',)), primitive=True),
                            Task(head=('factor_1_b', 'new_equation', ('factor_1_b',)), primitive=True),
                            Task(head=('factor_2_b', 'new_equation', 'factor_1_b', ('factor_2_b',)), primitive=True),
                            Task(head=('sum_factor', 'factor_1_b', 'factor_2_b', ('sum_factor',)), primitive=True),
                            Task(head=('sum_c', 'new_equation', 'sum_factor', ('sum_c',)), primitive=True),
                            Task(head=('new_first_expression', 'factor_1_b', 'factor_2_b', ('new_first_expression',)), primitive=True),
                            Task(head=('new_second_expression', 'new_first_expression', 'factor_1_b', 'factor_2_b', ('new_second_expression',)), primitive=True),
                            Task(head=('final_first_expression', V('equation'), ('final_first_expression',)), primitive=True),
                            Task(head=('final_second_expression', V('equation'), 'final_first_expression', ('final_second_expression',)), primitive=True),
                            Task(head=('final_answer', V('equation'), ('final_answer',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [   
                            Task(head=('a_value', V('equation'), ('a_value',)), primitive=True), 
                            Task(head=('b_value', V('equation'), ('b_value',)), primitive=True),
                            Task(head=('c_value', V('equation'), ('c_value',)), primitive=True),
                            Task(head=('ac_value', V('equation'), ('ac_value',)), primitive=True),
                            Task(head=('new_equation', V('equation'), ('new_equation',)), primitive=True),
                            Task(head=('new_b_value', 'new_equation', ('new_b_value',)), primitive=True),
                            Task(head=('new_c_value', 'new_equation', ('new_c_value',)), primitive=True),
                            Task(head=('final_first_expression', V('equation'), ('final_first_expression',)), primitive=True),
                            Task(head=('final_second_expression', V('equation'), 'final_first_expression', ('final_second_expression',)), primitive=True),
                            Task(head=('final_answer', V('equation'), ('final_answer',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [   
                            Task(head=('a_value', V('equation'), ('a_value',)), primitive=True), 
                            Task(head=('b_value', V('equation'), ('b_value',)), primitive=True),
                            Task(head=('c_value', V('equation'), ('c_value',)), primitive=True),
                            Task(head=('ac_value', V('equation'), ('ac_value',)), primitive=True),
                            Task(head=('final_first_expression', V('equation'), ('final_first_expression',)), primitive=True),
                            Task(head=('final_second_expression', V('equation'), 'final_first_expression', ('final_second_expression',)), primitive=True),
                            Task(head=('final_answer', V('equation'), ('final_answer',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [   
                            Task(head=('a_value', V('equation'), ('a_value',)), primitive=True), 
                            Task(head=('b_value', V('equation'), ('b_value',)), primitive=True),
                            Task(head=('c_value', V('equation'), ('c_value',)), primitive=True),
                            Task(head=('final_first_expression', V('equation'), ('final_first_expression',)), primitive=True),
                            Task(head=('final_second_expression', V('equation'), 'final_first_expression', ('final_second_expression',)), primitive=True),
                            Task(head=('final_answer', V('equation'), ('final_answer',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [   
                            Task(head=('final_first_expression', V('equation'), ('final_first_expression',)), primitive=True),
                            Task(head=('final_second_expression', V('equation'), 'final_first_expression', ('final_second_expression',)), primitive=True),
                            Task(head=('final_answer', V('equation'), ('final_answer',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],
                       

                      

                    ]
    ),
}
