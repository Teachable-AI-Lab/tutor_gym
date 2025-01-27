import argparse
from tutorgym.trainer import AuthorTrainer
from tutorgym.utils import DataShopLogger
from tutorgym.oracle_agent import OracleAgent
from tutorgym.envs.apprentice_tutors.tutor import AllTutorContainer

# Import all environment modules
from tutorgym.envs.apprentice_tutors.cognitive_models.logarithms import (
    htn_logarithms_quotient as logarithms_quotient,
    htn_logarithms_product as logarithms_product,
    htn_logarithms_power as logarithms_power,
)
from tutorgym.envs.apprentice_tutors.cognitive_models.radicals import (
    htn_radicals_adding_square_roots as radicals_add,
    htn_radicals_product_rule as radicals_product,
    htn_radicals_quotient_rule as radicals_quotient,
    htn_radicals_subtracting_square_roots as radicals_subtract
)

from tutorgym.envs.apprentice_tutors.cognitive_models.factoring import (
    factor_grouping as factor_grouping,
    factor_leading_one as factor_leading_one,
    factor_slip_slide as factor_slip_slide
)

from tutorgym.envs.apprentice_tutors.cognitive_models.logarithmic_equations import (
    htn_logarithmic_equations_solve_algebraically_before_after as logarithmic_equations_solve_algebraically_before_after,
    htn_logarithmic_equations_solve_algebraically as logarithmic_equations_solve_algebraically,
    htn_logarithmic_equations_solve_using_one_to_one_property as logarithmic_equations_solve_using_one_to_one_property
)

from tutorgym.envs.apprentice_tutors.cognitive_models.exponents import (
    htn_exponents_power as exponents_power,
    htn_exponents_product as exponents_product,
    htn_exponents_quotient as exponents_quotient
)

from tutorgym.envs.apprentice_tutors.cognitive_models.exponential_equations import (
    htn_exponential_equations_common_base as exponential_equations_common_base,
    htn_exponential_equations_different_base as exponential_equations_different_base,
    htn_exponential_equations_fractional_exponents_common_base as exponential_equations_fractional_exponents_common_base,
    htn_exponential_equations_solve_Aekt as exponential_equations_solve_Aekt,
    htn_exponential_equations_solve_quadratic_form as exponential_equations_solve_quadratic_form
)

from tutorgym.envs.apprentice_tutors.cognitive_models.quadratic_equations import (
    htn_quadratic_equations_identify_coeffs as quadratic_equations_identify_coeffs,
    htn_quadratic_equations_nature_of_solution as quadratic_equations_nature_of_solution,
    htn_quadratic_equations_solve_using_completing_square as quadratic_equations_solve_using_completing_square,
    htn_quadratic_equations_solve_using_factors as quadratic_equations_solve_using_factors,
    htn_quadratic_equations_solve_using_quadratic_formula as quadratic_equations_solve_using_quadratic_formula,
    htn_quadratic_equations_solve_using_square_root_property as quadratic_equations_solve_using_square_root_property
)

from tutorgym.envs.apprentice_tutors.cognitive_models.rational_equation import (
    htn_rational_equation_find_domain as rational_equation_find_domain
)

ENVIRONMENTS = {
    'logarithms_quotient': (logarithms_quotient.Domain, logarithms_quotient.htn_logarithms_quotient_problem),
    'logarithms_product': (logarithms_product.Domain, logarithms_product.htn_logarithms_product_rule_problem),
    'logarithms_power': (logarithms_power.Domain, logarithms_power.htn_logarithms_power_problem),
    'radicals_add': (radicals_add.Domain, radicals_add.htn_radicals_adding_square_roots_problem),
    'radicals_product': (radicals_product.Domain, radicals_product.htn_radicals_product_rule_problem),
    'radicals_quotient': (radicals_quotient.Domain, radicals_quotient.htn_radicals_quotient_rule_problem),
    'radicals_subtract': (radicals_subtract.Domain, radicals_subtract.htn_radicals_subtracting_square_roots_problem),
    'factor_grouping': (factor_grouping.Domain, factor_grouping.factor_grouping_problem),
    'factor_leading_one': (factor_leading_one.Domain, factor_leading_one.factor_leading_one_problem),
    'factor_slip_slide': (factor_slip_slide.Domain, factor_slip_slide.factor_slip_slide_problem),
    'logarithmic_equations_solve_algebraically_before_after': (logarithmic_equations_solve_algebraically_before_after.Domain, logarithmic_equations_solve_algebraically_before_after.htn_logarithmic_equations_solve_algebraically_before_after_problem),
    'logarithmic_equations_solve_algebraically': (logarithmic_equations_solve_algebraically.Domain, logarithmic_equations_solve_algebraically.htn_logarithmic_equations_solve_algebraically_problem),
    'logarithmic_equations_solve_using_one_to_one_property': (logarithmic_equations_solve_using_one_to_one_property.Domain, logarithmic_equations_solve_using_one_to_one_property.htn_logarithmic_equations_solve_using_one_to_one_property_problem),
    'exponents_power': (exponents_power.Domain, exponents_power.htn_exponents_power_problem),
    'exponents_product': (exponents_product.Domain, exponents_product.htn_exponents_product_problem),
    'exponents_quotient': (exponents_quotient.Domain, exponents_quotient.htn_exponents_quotient_problem),
    'exponential_equations_common_base': (exponential_equations_common_base.Domain, exponential_equations_common_base.htn_exponential_equations_common_base_problem),
    'exponential_equations_different_base': (exponential_equations_different_base.Domain, exponential_equations_different_base.htn_exponential_equations_different_base_problem),
    'exponential_equations_fractional_exponents_common_base': (exponential_equations_fractional_exponents_common_base.Domain, exponential_equations_fractional_exponents_common_base.htn_exponential_equations_fractional_exponents_common_base_problem),
    'exponential_equations_solve_Aekt': (exponential_equations_solve_Aekt.Domain, exponential_equations_solve_Aekt.htn_exponential_equations_solve_Aekt_problem),
    'exponential_equations_solve_quadratic_form': (exponential_equations_solve_quadratic_form.Domain, exponential_equations_solve_quadratic_form.htn_exponential_equations_solve_quadratic_form_problem),
    'quadratic_equations_identify_coeffs': (quadratic_equations_identify_coeffs.Domain, quadratic_equations_identify_coeffs.htn_quadratic_equations_identify_coeffs_problem),
    'quadratic_equations_nature_of_solution': (quadratic_equations_nature_of_solution.Domain, quadratic_equations_nature_of_solution.htn_quadratic_equations_nature_of_solution_problem),
    'quadratic_equations_solve_using_completing_square': (quadratic_equations_solve_using_completing_square.Domain, quadratic_equations_solve_using_completing_square.htn_quadratic_equations_solve_using_completing_square_problem),
    'quadratic_equations_solve_using_factors': (quadratic_equations_solve_using_factors.Domain, quadratic_equations_solve_using_factors.htn_quadratic_equations_solve_using_factors_problem),
    'quadratic_equations_solve_using_quadratic_formula': (quadratic_equations_solve_using_quadratic_formula.Domain, quadratic_equations_solve_using_quadratic_formula.htn_quadratic_equations_solve_using_quadratic_formula_problem),
    'quadratic_equations_solve_using_square_root_property': (quadratic_equations_solve_using_square_root_property.Domain, quadratic_equations_solve_using_square_root_property.htn_quadratic_equations_solve_using_square_root_property_problem),
    'rational_equation_find_domain': (rational_equation_find_domain.Domain, rational_equation_find_domain.htn_rational_equation_find_domain_problem)
}



def run_environment(env_name, n_problems=20):
    """
    Run a specific environment by name
    
    Args:
        env_name: String name of environment ('logarithms_quotient', 'radicals_product', etc.)
        n_problems: Number of problems to run
    """
    if env_name not in ENVIRONMENTS:
        raise ValueError(f"Environment {env_name} not found. Available environments: {list(ENVIRONMENTS.keys())}")
        
    domain, problem_generator = ENVIRONMENTS[env_name]
    
    logger = DataShopLogger(env_name, extra_kcs=['field'], output_dir=f'log_{env_name}_author')
    env = AllTutorContainer(domain=domain, problem_generator=problem_generator, problem_types=["power"])
    agent = OracleAgent(env)
    trainer = AuthorTrainer(agent, env, logger=logger, n_problems=n_problems)
    trainer.start()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run apprentice tutor environments')
    parser.add_argument('--env', type=str, choices=list(ENVIRONMENTS.keys()), default='logarithms_quotient',
                      help='Look at code for environment names (logarithms_quotient, radicals_product, etc.)')
    parser.add_argument('--problems', type=int, default=20,
                      help='Number of problems to run')
    
    args = parser.parse_args()
    run_environment(args.env, args.problems)
