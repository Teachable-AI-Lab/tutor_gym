from pathlib import Path
from tutorgym.env_classes.CTAT.CTAT_problem_set import collect_CTAT_problem_sets
import random
import json
import os
import sys
from typing import Union


def _resolve_n_domain_probs(domain, x):
    if(isinstance(x, dict)):
        return x.get(domain, None)
    else:
        return x

# Frequences of problems-per-domain solved by at least 4 students in apprentice data 
APPRENTICE_FREQ_PER_DOMAIN = {'factor_grouping': 12, 'factor_leading_one': 15, 'factor_slip_slide': 10, 'logarithmic_equations_solve_algebraically_before_after': 4, 'logarithms_quotient': 8, 'quadratic_equations_identify_coeffs': 2, 'radicals_product_rule': 4, 'logarithms_power': 6, 'exponents_product': 8, 'quadratic_equations_solve_using_factors': 2, 'radicals_adding_square_roots': 2, 'radicals_quotient_rule': 5, 'rational_equation_find_domain': 10, 'exponential_equations_different_base': 2, 'exponential_equations_fractional_exponents_common_base': 0, 'logarithmic_equations_solve_algebraically': 4, 'logarithms_product': 10, 'quadratic_equations_factorize': 2, 'exponential_equations_common_base': 2, 'exponential_equations_solve_Aekt': 1, 'logarithmic_equations_solve_using_one_to_one_property': 4, 'quadratic_equations_solve_using_completing_square': 0, 'radicals_subtracting_square_roots': 4, 'quadratic_equations_nature_of_solution': 3, 'exponential_equations_change_to_common_base': 1, 'exponential_equations_solve_quadratic_form': 2, 'quadratic_equations_solve_using_quadratic_formula': 1, 'quadratic_equations_solve_using_square_root_property': 2}

def collect_apprentice_problems(
        domains=None,
        problems_per_domain : Union[int,dict] = APPRENTICE_FREQ_PER_DOMAIN,
        random_seed=10):

    random.seed(random_seed)

    from tutorgym.envs.apprentice.env_registry import ENVIRONMENTS
    if(domains is None):
        domains = list(APPRENTICE_FREQ_PER_DOMAIN.keys())

    problem_set = []
    for domain in domains:
        clean_domain = domain.replace("htn_", "")

        if clean_domain not in ENVIRONMENTS:
            raise ValueError(f"Environment {clean_domain} not found. Available environments: {list(ENVIRONMENTS.keys())}")
        _, problem_generator = ENVIRONMENTS[clean_domain]

        n_prob = _resolve_n_domain_probs(domain, problems_per_domain)

        for i in range(n_prob):
            problem_set.append({
                "domain": domain,
                "initial_problem" : problem_generator(),
                "scaffold" : "first", 
            })

    random.seed(None)

    return problem_set


def collect_oatutor_problems(
        domains=None,
        problems_per_domain : Union[None,int,dict] = 2,
        random_seed=10):

    random.seed(random_seed)

    current_dir = Path(__file__).parent

    if(domains is None):
        problem_names_file = os.path.join(current_dir, '../envs/oatutor/ProblemNames.txt')
        with open(problem_names_file, 'r') as file:
            domains = [line.strip() for line in file if line.strip()]

    problem_pool_dir = os.path.join(current_dir, '../envs/oatutor/ProblemPool')
    # problems = os.listdir(problem_pool_dir)

    problem_names = []

    for domain in domains:
        problems = [d for d in os.listdir(problem_pool_dir) 
                    if domain in d and os.path.isdir(os.path.join(problem_pool_dir, d))]

        if(random_seed is not None):
            random.shuffle(problems)

        n_prob = _resolve_n_domain_probs(domain, problems_per_domain)
        problem_names += problems[:n_prob]

    print(problem_names)

    problem_set = [{"problem_name" : p} for p in problem_names]

    # Deseed 'random' so it doesn't infect other random things
    random.seed(None)
    return problem_set


def collect_ctat_problems(
        domain_dirs=None, 
        problems_per_domain : Union[None,int,dict] =None,
        random_seed=10):

    from tutorgym.envs.CTAT.Mathtutor.env_registry import WORKING_DOMAINS

    if(domain_dirs==None):
        domain_dirs = [f"../envs/CTAT/Mathtutor/{d}/" for d in WORKING_DOMAINS]

    problems = []
    for domain_dir in domain_dirs:
        domain = os.path.split(domain_dir)[-1]

        problem_sets = collect_CTAT_problem_sets(domain_dir)
        for prob_set in problem_sets:
            prob_set = list(prob_set)
            if(random_seed is not None):
                random.shuffle(prob_set)

            n_prob = _resolve_n_domain_probs(domain, problems_per_domain)
            prob_set = prob_set[:n_prob]
            for problem in prob_set:
                problems.append(problem)
    return problems
