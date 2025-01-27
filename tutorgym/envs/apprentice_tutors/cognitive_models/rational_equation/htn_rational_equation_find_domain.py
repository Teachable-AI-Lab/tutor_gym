import sympy as sp
from random import randint, choice

import sympy as sp
from sympy import sstr, latex, symbols
from sympy.parsing.latex._parse_latex_antlr import parse_latex
import re
from functools import reduce
from random import randint, random
from shop2.domain import Task, Operator, Method
# from shop2.planner import SHOP2
from shop2.fact import Fact
from shop2.conditions import Filter
from shop2.common import V


import math

def solve_quadratic(equation):
    # Parse the equation to extract coefficients
    x = sp.symbols('x')
    match = re.search(r'{\d}({.*?})', equation)
    expression = match.group(1)
    expression = expression.replace('^', '**').replace('{','').replace('}','')
    expression = re.sub(r'([a-zA-Z0-9])([a-zA-Z])', r'\1*\2', expression)
    denominator = sp.sympify(expression)
    
    # Get the coefficients of the quadratic equation
    coeff = sp.Poly(denominator, x).all_coeffs()
    a, b, c = coeff[0], coeff[1], coeff[2]

    # Calculate the solutions using the quadratic formula
    discriminant = b**2 - 4*a*c
    solution1 = (-b + sp.sqrt(discriminant)) / (2*a)
    solution2 = (-b - sp.sqrt(discriminant)) / (2*a)
    return solution2, solution1

def factors(n):
    fset = set(reduce(list.__add__,
               ([i, n//i] for i in range(1, int(abs(n)**0.5) + 1)
                if n % i == 0)))

    other_signs = set([-1 * f for f in fset])
    fset = fset.union(other_signs)

    return fset
    
def htn_rational_equation_find_domain_problem():
    n1 = 1

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
        return htn_rational_equation_find_domain_problem()

    if b_value > 0:
        problem += "+"

    problem += "{}x".format(b_value)

    c_value = n2 * n4
    if c_value > 0:
        problem += "+"

    problem += "{}".format(c_value)
    
    # return 'f(x)=\\frac{1}{x^2-6x+9}}'
    return "f(x)=\\frac{" + "1"  + "}" + "{" + problem + "}" + "}"

def denominator_set_zero(init_value): 
        x = symbols("x")
        c1, c0 = re.findall(r'\d+', init_value)[2:]
        equation = ""
        if re.search(f'-{re.escape(c0)}', init_value):
            if re.search(f'-{re.escape(c1)}', init_value):
                equation = f"Eq((x**2 - {c1}*x) - {c0}, 0)"
            else:
                equation = f"Eq((x**2 + {c1}*x) - {c0}, 0)"
        else:
            if re.search(f'-{re.escape(c1)}', init_value):
                equation = f"Eq((x**2 - {c1}*x) + {c0}, 0)"
            else:
                equation = f"Eq((x**2 + {c1}*x) + {c0}, 0)"
    
        answer = re.compile(re.sub(r'([-+()*])', r'\\\1', sp.sstr(equation, order="grlex").replace("1*", "")))
        hint = ""
        if re.search(f'-{re.escape(c0)}', init_value):
            if re.search(f'-{re.escape(c1)}', init_value):
                hint = latex(sp.Eq((x**2 - int(c1)*x)-int(c0), 0)).replace("-1*", "-")
            else:
                hint = latex(sp.Eq((x**2 + int(c1)*x)-int(c0), 0)).replace("-1*", "-")
        else:
            if re.search(f'-{re.escape(c1)}', init_value):
                hint = latex(sp.Eq((x**2 - int(c1)*x)+int(c0), 0)).replace("-1*", "-")
            else:
                hint = latex(sp.Eq((x**2 + int(c1)*x)+int(c0), 0)).replace("-1*", "-")
        return tuple([(answer, hint)])
        

def factor_trinomial(init_value):
    x = symbols("x")
    c1, c0 = re.findall(r'\d+', init_value)[2:]
    if re.search(f'-{re.escape(c0)}', init_value):
        c0 = -int(c0)
    else:
        c0 = int(c0)
    if re.search(f'-{re.escape(c1)}', init_value):
        c1 = -int(c1)
    else:
        c1 = int(c1)

    equation = x**2 + c1*x + c0
    answer = sp.Eq(sp.factor(equation), 0)
    hint = latex(answer)
    answer = re.compile(re.sub(r'([-+()*])', r'\\\1', sp.sstr(answer, order="grlex")))
    return tuple([(answer, hint)])

def zero_product_left(init_value):
    x = symbols("x")
    c1, c0 = re.findall(r'\d+', init_value)[2:]
    if re.search(f'-{re.escape(c0)}', init_value):
        c0 = -int(c0)
    else:
        c0 = int(c0)
    if re.search(f'-{re.escape(c1)}', init_value):
        c1 = -int(c1)
    else:
        c1 = int(c1)

    equation = x**2 + c1*x + c0
    factors = sp.factor(equation)
    if factors.args[1] == 2:
        answer = sp.Eq(factors.args[0], 0)
        hint = latex(answer)
        answer = re.compile(re.sub(r'([-+()*])', r'\\\1', sp.sstr(answer, order="grlex")))
        return tuple([(answer, hint)])
    else:
        facts = list()
        for factor in factors.args:
            answer = sp.Eq(factor, 0)
            hint = latex(answer)
            answer = re.compile(re.sub(r'([-+()*])', r'\\\1', sp.sstr(answer, order="grlex")))
            facts.append((answer, hint))
        return tuple(facts)
    


def zero_product_right(init_value, factor):
    x = symbols("x")
    c1, c0 = re.findall(r'\d+', init_value)[2:]
    if re.search(f'-{re.escape(c0)}', init_value):
        c0 = -int(c0)
    else:
        c0 = int(c0)
    if re.search(f'-{re.escape(c1)}', init_value):
        c1 = -int(c1)
    else:
        c1 = int(c1)

    equation = x**2 + c1*x + c0
    first_part = parse_latex(factor)
    answer = sp.div(equation, first_part)[0]
    answer = sp.Eq(answer, 0)
    hint = latex(answer)
    answer = re.compile(re.sub(r'([-+()*])', r'\\\1', sp.sstr(answer, order="grlex")))
    return tuple([(answer, hint)])
    
def solve_left(init_value):
    x = symbols("x")
    c1, c0 = re.findall(r'\d+', init_value)[2:]
    if re.search(f'-{re.escape(c0)}', init_value):
        c0 = -int(c0)
    else:
        c0 = int(c0)
    if re.search(f'-{re.escape(c1)}', init_value):
        c1 = -int(c1)
    else:
        c1 = int(c1)

    equation = sp.Eq(x**2 + c1*x + c0, 0)
    equation = sp.factor(equation)
    facts = list()
    if equation.lhs.args[1] == 2:
        factor_eq = sp.Eq(equation.lhs.args[0], 0)
        root = sp.Eq(x, sp.solve(factor_eq, x)[0])
        answer = re.compile(re.sub(r'([-+^()*])', r'\\\1', sstr(root, order="grlex")))
        hint = latex(root)
        value = tuple([(answer, hint)])

    else:
        facts = list()
        for factor in equation.lhs.args:
            factor = sp.Eq(factor, 0)
            root = sp.Eq(x, sp.solve(factor, x)[0])
            answer = re.compile(re.sub(r'([-+()*])', r'\\\1', sp.sstr(root, order="grlex")))
            hint = latex(root)
            facts.append((answer, hint))
        value = tuple(facts)
    return value

def solve_right(init_value, factor):
    x = symbols("x")
    c1, c0 = re.findall(r'\d+', init_value)[2:]
    if re.search(f'-{re.escape(c0)}', init_value):
        c0 = -int(c0)
    else:
        c0 = int(c0)
    if re.search(f'-{re.escape(c1)}', init_value):
        c1 = -int(c1)
    else:
        c1 = int(c1)

    equation = sp.Eq(x**2 + c1*x + c0, 0)
    feq = parse_latex(factor).lhs-parse_latex(factor).rhs
    quotient = sp.Eq(sp.div(equation, feq)[0],0)
    root = sp.Eq(x, sp.solve(quotient, x)[0])
    answer = re.compile(re.sub(r'([-+()*])', r'\\\1', sp.sstr(root, order="grlex")))
    hint = latex(root)
    value = tuple([(answer, hint)])
    return value

def domain_left(init_value):
    x = symbols("x")
    c1, c0 = re.findall(r'\d+', init_value)[2:]
    if re.search(f'-{re.escape(c0)}', init_value):
        c0 = -int(c0)
    else:
        c0 = int(c0)
    if re.search(f'-{re.escape(c1)}', init_value):
        c1 = -int(c1)
    else:
        c1 = int(c1)

    equation = sp.Eq(x**2 + c1*x + c0, 0)
    equation = sp.factor(equation)
    facts = list()
    const, factors = sp.factor(equation.lhs).as_coeff_mul()   
    if len(factors) == 1:
        factors = (factors[0].args[0], factors[0].args[0])
    for i in range(2):
        factorized = sp.Eq(sp.Mul(const, factors[i])*factors[(i+1)%2], 0)
        for factor in factorized.lhs.as_coeff_mul()[1]:
            equation = sp.Eq(factor,0)  
            root = sp.solve(equation, x)[0]
            answer = re.compile(sp.sstr(root, order="grlex"))
            hint = root
            facts.append((answer, hint))
    return tuple(facts)

def domain_right(init_value, factor):
    x = symbols("x")
    c1, c0 = re.findall(r'\d+', init_value)[2:]
    if re.search(f'-{re.escape(c0)}', init_value):
        c0 = -int(c0)
    else:
        c0 = int(c0)
    if re.search(f'-{re.escape(c1)}', init_value):
        c1 = -int(c1)
    else:
        c1 = int(c1)

    equation = sp.Eq(x**2 + c1*x + c0, 0)
    feq = x-int(factor)
    quotient = sp.Eq(sp.div(equation, feq)[0],0)
    root = sp.solve(quotient, x)[0]
    answer = re.compile(re.sub(r'([-+()*])', r'\\\1', sp.sstr(root, order="grlex")))
    hint = latex(root)
    value = tuple([(answer, hint)])
    return value


Domain = {
    'done': Operator(head=('done', V('kc')),
                     precondition=[Fact(start=True)],
                     effects=[Fact(field='done', value=((re.compile('x'),),), kc=V('kc'), answer=True)],
    ),
    'denominator_set_zero': Operator(head=('denominator_set_zero', V('equation'), V('kc')),
                                        precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                                        effects=[Fact(field='denominator_set_zero', value=(denominator_set_zero, V('eq')), kc=V('kc'), answer=True)],
    ),

    'factor_trinomial': Operator(head=('factor_trinomial', V('equation'), V('kc')),
                                    precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                                    effects=[Fact(field='factor_trinomial', value=(factor_trinomial, V('eq')), kc=V('kc'), answer=True)],
    ),  

    'zero_product_left': Operator(head=('zero_product_left', V('equation'), V('kc')),
                                precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                                effects=[Fact(field='zero_product_left', value=(zero_product_left, V('eq')), kc=V('kc'), answer=True)],
    ),

    'zero_product_right': Operator(head=('zero_product_right', V('equation'), V('factor'), V('kc')),
                                precondition=Fact(field=V('equation'), value=V('eq'), answer=False)&
                                             Fact(field=V('factor'), value=V('feq'), kc=V('fkc'), answer=True),
                                effects=[Fact(field='zero_product_right', value=(zero_product_right, V('eq'), V('feq')), kc=V('kc'), answer=True)],
    ),

    'solve_left': Operator(head=('solve_left', V('equation'), V('kc')),
                        precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                        effects=[Fact(field='solve_left', value=(solve_left, V('eq')), kc=V('kc'), answer=True)],
    ),

    'solve_right': Operator(head=('solve_right', V('equation'), V('factor'), V('kc')),
                        precondition=Fact(field=V('equation'), value=V('eq'), answer=False)&
                                        Fact(field=V('factor'), value=V('feq'), kc=V('fkc'), answer=True),
                        effects=[Fact(field='solve_right', value=(solve_right, V('eq'), V('feq')), kc=V('kc'), answer=True)],
    ),

    'domain_left': Operator(head=('domain_left', V('equation'), V('kc')),
                        precondition=Fact(field=V('equation'), value=V('eq'), answer=False),
                        effects=[Fact(field='domain_left', value=(domain_left, V('eq')), kc=V('kc'), answer=True)],
    ),

    'domain_right': Operator(head=('domain_right', V('equation'), V('factor'), V('kc')),
                        precondition=Fact(field=V('equation'), value=V('eq'), answer=False)&
                                     Fact(field=V('factor'), value=V('feq'), kc=V('fkc'), answer=True),
                        effects=[Fact(field='domain_right', value=(domain_right, V('eq'), V('feq')), kc=V('kc'), answer=True)],
    ),
    'solve': Method(head=('solve', V('equation')),
                    preconditions=[
                        Fact(scaffold='level_4'),
                        Fact(scaffold='level_3'),
                        Fact(scaffold='level_2'),
                        Fact(scaffold='level_1'),
                        Fact(scaffold='level_0'),
                    ],
                    subtasks=[
                        [
                            Task(head=('denominator_set_zero', V('equation'), ('denominator_set_zero',)), primitive=True),
                            Task(head=('factor_trinomial', V('equation'), ('factor_trinomial',)), primitive=True),
                            Task(head=('zero_product_left', V('equation'), ('zero_product_left',)), primitive=True),
                            Task(head=('zero_product_right', V('equation'), 'zero_product_left', ('zero_product_right',)), primitive=True),
                            Task(head=('solve_left', V('equation'), ('solve_left',)), primitive=True),
                            Task(head=('solve_right', V('equation'), 'solve_left', ('solve_right',)), primitive=True),
                            Task(head=('domain_left', V('equation'), ('domain_left',)), primitive=True),
                            Task(head=('domain_right', V('equation'), 'domain_left', ('domain_right',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [
                            Task(head=('denominator_set_zero', V('equation'), ('denominator_set_zero',)), primitive=True),
                            Task(head=('factor_trinomial', V('equation'), ('factor_trinomial',)), primitive=True),
                            Task(head=('zero_product_left', V('equation'), ('zero_product_left',)), primitive=True),
                            Task(head=('zero_product_right', V('equation'), 'zero_product_left', ('zero_product_right',)), primitive=True),
                            Task(head=('domain_left', V('equation'), ('domain_left',)), primitive=True),
                            Task(head=('domain_right', V('equation'), 'domain_left', ('domain_right',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [
                            Task(head=('denominator_set_zero', V('equation'), ('denominator_set_zero',)), primitive=True),
                            Task(head=('factor_trinomial', V('equation'), ('factor_trinomial',)), primitive=True),
                            Task(head=('domain_left', V('equation'), ('domain_left',)), primitive=True),
                            Task(head=('domain_right', V('equation'), 'domain_left', ('domain_right',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [
                            Task(head=('denominator_set_zero', V('equation'), ('denominator_set_zero',)), primitive=True),
                            Task(head=('domain_left', V('equation'), ('domain_left',)), primitive=True),
                            Task(head=('domain_right', V('equation'), 'domain_left', ('domain_right',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],

                        [
                            Task(head=('domain_left', V('equation'), ('domain_left',)), primitive=True),
                            Task(head=('domain_right', V('equation'), 'domain_left', ('domain_right',)), primitive=True),
                            Task(head=('done', ('done',)), primitive=True)
                        ],
                    ]
    ),
}