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

ENVIRONMENTS = {
    'logarithms_quotient': (logarithms_quotient.Domain, logarithms_quotient.htn_logarithms_quotient_problem),
    'logarithms_product': (logarithms_product.Domain, logarithms_product.htn_logarithms_product_rule_problem),
    'logarithms_power': (logarithms_power.Domain, logarithms_power.htn_logarithms_power_problem),
    'radicals_add': (radicals_add.Domain, radicals_add.htn_radicals_adding_square_roots_problem),
    'radicals_product': (radicals_product.Domain, radicals_product.htn_radicals_product_rule_problem),
    'radicals_quotient': (radicals_quotient.Domain, radicals_quotient.htn_radicals_quotient_rule_problem),
    'radicals_subtract': (radicals_subtract.Domain, radicals_subtract.htn_radicals_subtracting_square_roots_problem)
}

def run_environment(env_name, n_problems=20):
    """
    Run a specific environment by name
    
    Args:
        env_name: String name of environment ('quotient', 'product', or 'power')
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
