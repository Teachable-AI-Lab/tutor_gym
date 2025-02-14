import argparse
from tutorgym.trainer import AuthorTrainer
from tutorgym.utils import DataShopLogger
from tutorgym.agents.oracle_agent import OracleAgent
# from tutorgym.envs.apprentice_tutors.tutor import AllTutorContainer
from tutorgym.env_classes.apprentice_tutor import ApprenticeTutor
from tutorgym.envs.apprentice_tutors.env_registry import ENVIRONMENTS



def run_environment(domain_name, n_problems=20, problem_set=[], scaffold="first"):
    """
    Run a specific environment by name
    
    Args:
        env_name: String name of environment ('logarithms_quotient', 'radicals_product', etc.)
        n_problems: Number of problems to run
    """
    if domain_name not in ENVIRONMENTS:
        raise ValueError(f"Environment {domain_name} not found. Available environments: {list(ENVIRONMENTS.keys())}")
        
    # domain, problem_generator = ENVIRONMENTS[env_name]
    
    logger = DataShopLogger(domain_name, extra_kcs=['field'], output_dir=f'log_{domain_name}_author')
    env = ApprenticeTutor(domain=domain_name, scaffold=scaffold)
    # env.htn_model.scaffold = scaffold

    agent = OracleAgent(env)
    trainer = AuthorTrainer(agent, env, logger=logger,
                problem_set=problem_set, n_problems=n_problems)
    trainer.start()

if __name__ == "__main__":
    # parser = argparse.ArgumentParser(description='Run apprentice tutor environments')
    # parser.add_argument('--env', type=str, choices=list(ENVIRONMENTS.keys()), default='logarithms_quotient',
    #                   help='Look at code for environment names (logarithms_quotient, radicals_product, etc.)')
    # parser.add_argument('--problems', type=int, default=20,
    #                   help='Number of problems to run')
    
    # args = parser.parse_args()
    # run_environment(args.env, args.problems)
    # run_environment("exponents_power", 1, None)
    # run_environment("logarithms_power", 1, "first")
    # run_environment("exponents_quotient", 1, [{"initial_problem": "\\frac{816^{12}}{816^{3}}"}])        

    # raise ValueError()

    for env in ENVIRONMENTS:
        # print(env)
        try:
            run_environment(env, 1)        
            print("SUCESS", env)
        except Exception as e:
            print("FAILED", env)
            raise e
        print()


