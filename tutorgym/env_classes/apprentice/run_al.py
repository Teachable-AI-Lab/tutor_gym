from tutorgym.env_classes.apprentice.apprentice_tutor import ApprenticeTutor
from tutorgym.trainer import Trainer
from tutorgym.utils import DataShopLogger
from tutorgym.env_classes.apprentice.test_scaffolding import ScaffoldIterator

class SimpleInterleaveController:
    def __init__(self, problem_list, max_cycles=1):
        self.problem_list = problem_list
        self.index = 0
        self.max_cycles = max_cycles
        self.count = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.count >= self.max_cycles * len(self.problem_list):
            raise StopIteration
        prob = self.problem_list[self.index]
        self.index = (self.index + 1) % len(self.problem_list)
        self.count += 1
        return prob


POWER_PROBLEMS = [
    {"domain": "exponents_power", "initial_problem": "(5^3)^4"},
    {"domain": "exponents_power", "initial_problem": "(2^6)^2"},
    {"domain": "exponents_power", "initial_problem": "(9^2)^5"},
    {"domain": "exponents_power", "initial_problem": "(7^4)^3"},
]

PRODUCT_PROBLEMS = [
    {"domain": "exponents_product", "initial_problem": "5^3 * 5^7"},
    {"domain": "exponents_product", "initial_problem": "3^8 * 3^2"},
    {"domain": "exponents_product", "initial_problem": "11^5 * 11^4"},
    {"domain": "exponents_product", "initial_problem": "6^9 * 6^3"},
]

QUOTIENT_PROBLEMS = [
    {"domain": "exponents_quotient", "initial_problem": "8^12 / 8^4"},
    {"domain": "exponents_quotient", "initial_problem": "10^9 / 10^3"},
    {"domain": "exponents_quotient", "initial_problem": "4^7 / 4^2"},
    {"domain": "exponents_quotient", "initial_problem": "12^6 / 12^1"},
]

EXPONENT_PROBLEMS = POWER_PROBLEMS + PRODUCT_PROBLEMS + QUOTIENT_PROBLEMS


def run_training(agent, domain='exponents_product', initial_problem=None,
                 scaffold='all', logger_name=None, n_problems=10,
                 interleave=False, n_cycles=1):
    
    if logger_name is None:
        scaffold_str = ScaffoldIterator.get_scaffold_name(scaffold).replace(' ', '_')
        if interleave:
            logger_name = f'apprentice_interleaved_{scaffold_str}'
        else:
            logger_name = f'apprentice_{domain}_{scaffold_str}'

    logger = DataShopLogger(logger_name, extra_kcs=['field'], output_dir='log_al')

    init_scaffold = scaffold if scaffold != 'all' else 'first'
    env = ApprenticeTutor(
        domain=domain,
        initial_problem=initial_problem,
        scaffold=init_scaffold,
    )
    if scaffold == 'all':
        env.scaffold = 'all'

    if interleave:
        controller = SimpleInterleaveController(EXPONENT_PROBLEMS, max_cycles=n_cycles)
        trainer = Trainer(agent, env, logger=logger, outer_loop_controller=controller)
    else:
        trainer = Trainer(agent, env, logger=logger, n_problems=n_problems)

    trainer.start()


if __name__ == "__main__":
    import sys
    import argparse
    import faulthandler
    faulthandler.enable()

    parser = argparse.ArgumentParser(
        description='Run Apprentice Learner agents through scaffolded problems')
    
    parser.add_argument('--n-agents', default=1, type=int, metavar="<n_agents>",
                        dest="n_agents", help="number of agents to train")
    parser.add_argument('--n-problems', default=100, type=int, metavar="<n_problems>",
                        dest="n_problems", help="number of problems per agent")
    parser.add_argument('--agent-type', default='DIPL', metavar="<agent_type>",
                        dest="agent_type", help="type of agent: DIPL (CREAgent), MODULAR, or RHS_LHS")
    parser.add_argument('--domain', default='exponents_product', metavar="<domain>",
                        dest="domain", help="domain name from env_registry (e.g., exponents_product)")
    parser.add_argument('--scaffold', default='all', metavar="<scaffold>",
                        dest="scaffold",
                        help="scaffolding level: 'all' (full), 'none' (no scaffolding), or specific level")
    parser.add_argument('--initial-problem', default=None, metavar="<problem>",
                        dest="initial_problem", help="initial problem string (optional)")
    parser.add_argument('--interleave', action='store_true', default=False,
                        dest="interleave",
                        help="interleave product, quotient, and power problems")
    parser.add_argument('--n-cycles', default=1, type=int, metavar="<n_cycles>",
                        dest="n_cycles",
                        help="number of full cycles through the interleaved problem list")
    
    args = parser.parse_args(sys.argv[1:])
    
    scaffold = None if args.scaffold.lower() == 'none' else args.scaffold

    scaffold_str = ScaffoldIterator.get_scaffold_name(scaffold).replace(' ', '_')
    if args.interleave:
        logger_name = f'interleaved_{args.agent_type}_{scaffold_str}_{args.n_cycles}cycles'
    else:
        logger_name = f'{args.domain}_{args.agent_type}_{scaffold_str}_{args.n_problems}probs'

    print(f"Training {args.n_agents} agents")
    if args.interleave:
        print(f"Mode: interleaved (product / quotient / power), {args.n_cycles} cycle(s)")
    else:
        print(f"Domain: {args.domain}")
    print(f"Scaffolding: {ScaffoldIterator.get_scaffold_name(scaffold)}")
    print(f"Agent type: {args.agent_type}")

    if not args.interleave:
        print(f"Problems per agent: {args.n_problems}")
    print()
    
    for agent_num in range(args.n_agents):
        print(f"Starting agent {agent_num + 1}/{args.n_agents}")
        
        if args.agent_type.upper() == "DIPL":
            try:
                from apprentice.agents.cre_agents.cre_agent import CREAgent
                import tutorgym.helpers.ai2t_helpers 
            except (ImportError, ModuleNotFoundError) as e:
                print(f"\nError: Could not import apprentice learner package.")
                print(f"Make sure the apprentice learner framework is installed.")
                print(f"Original error: {e}\n")
                sys.exit(1)
            
            agent_args = {
                "search_depth": 2,
                "where_learner": "mostspecific",
                "when_learner": "decision_tree",
                "which_learner": "when_prediction",
                "action_chooser": "max_which_utility",
                "suggest_uncert_neg": True,
                "planner": "set_chaining",
                "explanation_choice": "least_operations",
                "error_on_bottom_out": False,
                "extra_features": ["Match"],
                "when_args": {"encode_relative": True, "one_hot": True},
                "should_find_neighbors": True,
                "function_set": ["PowerRule","MultiplyExponents","ProductRule","SimplifyProduct"],
                "feature_set": ['Equals'],
            }
            agent = CREAgent(**agent_args)
            
        elif args.agent_type.upper() == "MODULAR":
            try:
                from apprentice.agents.ModularAgent import ModularAgent
                import tutorgym.helpers.ai2t_helpers  
            except (ImportError, ModuleNotFoundError) as e:
                print(f"\nError: Could not import apprentice learner package.")
                print(f"Make sure the apprentice learner framework is installed.")
                print(f"Original error: {e}\n")
                sys.exit(1)
            agent_args = {
                "search_depth": 2,
                "where_learner": "mostspecific",
                "when_learner": "decisiontree2",
                "planner": "set_chaining",
                "explanation_choice": "least_operations",
                "state_variablization": "metaskill",
                "strip_attrs": ["to_left", "to_right", "above", "below", 
                               "type", "id", "offsetParent", "dom_class"],
                "should_find_neighbors": True,
            }
            agent = ModularAgent(**agent_args)
            
        elif args.agent_type.upper() == "RHS_LHS":
            try:
                from apprentice.agents.RHS_LHS_Agent import RHS_LHS_Agent
                import tutorgym.helpers.ai2t_helpers
            except (ImportError, ModuleNotFoundError) as e:
                print(f"\nError: Could not import apprentice learner package.")
                print(f"Make sure the apprentice learner framework is installed.")
                print(f"Original error: {e}\n")
                sys.exit(1)
            agent = RHS_LHS_Agent()
            
        else:
            raise ValueError(f"Unrecognized agent type {args.agent_type!r}. "
                           f"Use DIPL, MODULAR, or RHS_LHS.")
        
        run_training(
            agent=agent,
            domain=args.domain,
            initial_problem=args.initial_problem,
            scaffold=scaffold,
            logger_name=logger_name,
            n_problems=args.n_problems,
            interleave=args.interleave,
            n_cycles=args.n_cycles,
        )


        print(f"Completed agent {agent_num + 1}/{args.n_agents}")
        print()
    
    print(f"All {args.n_agents} agents completed!")
