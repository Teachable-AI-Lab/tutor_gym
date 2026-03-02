from tutorgym.env_classes.apprentice.apprentice_tutor import ApprenticeTutor
from tutorgym.trainer import Trainer
from tutorgym.utils import DataShopLogger
from tutorgym.env_classes.apprentice.test_scaffolding import ScaffoldIterator


def run_training(agent, domain='exponents_product', initial_problem=None, 
                 scaffold='all', logger_name=None, n_problems=10):
    """Run apprentice learner training on a specific domain with scaffolding."""
    if logger_name is None:
        scaffold_str = ScaffoldIterator.get_scaffold_name(scaffold).replace(' ', '_')
        logger_name = f'apprentice_{domain}_{scaffold_str}'
    
    logger = DataShopLogger(logger_name, extra_kcs=['field'], output_dir='log_al')
    env = ApprenticeTutor(
        domain=domain,
        initial_problem=initial_problem,
        scaffold=scaffold if scaffold != 'all' else 'first'
    )
    
    if scaffold == 'all':
        env.scaffold = 'all'
    
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
    
    args = parser.parse_args(sys.argv[1:])
    
    scaffold = None if args.scaffold.lower() == 'none' else args.scaffold
    
    scaffold_str = ScaffoldIterator.get_scaffold_name(scaffold).replace(' ', '_')
    logger_name = f'{args.domain}_{args.agent_type}_{scaffold_str}_{args.n_problems}probs'
    
    print(f"Training {args.n_agents} agents on {args.domain}")
    print(f"Scaffolding: {ScaffoldIterator.get_scaffold_name(scaffold)}")
    print(f"Agent type: {args.agent_type}")
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
            n_problems=args.n_problems
        )


        print(f"Completed agent {agent_num + 1}/{args.n_agents}")
        print()
    
    print(f"All {args.n_agents} agents completed!")
