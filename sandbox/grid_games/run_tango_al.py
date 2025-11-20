import sys
import os
# Add workspace root to Python path so tutorgym and apprentice can be imported
workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)
# Add AL_Core to path for apprentice imports
al_core_path = os.path.join(workspace_root, 'AL_Core')
if al_core_path not in sys.path:
    sys.path.insert(0, al_core_path)

from apprentice.agents.cre_agents.cre_agent import CREAgent
import tutorgym.helpers.ai2t_helpers # Registers SkillApplication -> Action
# Import environment module to register Tango fact types and action types
from apprentice.agents.cre_agents import environment
from tutorgym.env_classes.misc.fraction_arith.fractions import FractionArithmetic
from tutorgym.trainer import Trainer, AuthorTrainer
from tutorgym.utils import DataShopLogger
from sandbox.grid_games.tango_env import TangoPuzzle

import time
import argparse
import faulthandler
faulthandler.enable()

def run_training(agent, grid_size=6, problem_types=["basic"], logger_name=None, n=10):
    if logger_name is None:
        logger_name = f"Tango_{grid_size}x{grid_size}"
    
    logger = DataShopLogger(logger_name, extra_kcs=['field'], output_dir='log_tango_al')
    env = TangoPuzzle(grid_size=grid_size, problem_types=problem_types)
    trainer = Trainer(agent, env, logger=logger, n_problems=n)
    trainer.start()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Runs AL agents on Tango puzzle')
    parser.add_argument('--n-agents', default=50, type=int, metavar="<n_agents>",
                        dest="n_agents", help="number of agents")
    parser.add_argument('--n-problems', default=500, type=int, metavar="<n_problems>",
                        dest="n_problems", help="number of problems")
    parser.add_argument('--grid-size', default=6, type=int, metavar="<grid_size>",
                        dest="grid_size", help="size of the grid")
    parser.add_argument('--agent-type', default='DIPL', metavar="<agent_type>",
                        dest="agent_type", help="type of agents DIPL or RHS_LHS")
    parser.add_argument('--problem-types', default=["basic"], nargs='+', metavar="<problem_types>",
                        dest="problem_types", help="problem types (default: ['basic'])")

    args = parser.parse_args(sys.argv[1:])

    print("n_agents", args.n_agents)
    print("grid_size", args.grid_size)
    print("problem_types", args.problem_types)
    
    logger_name = f'tango_{args.grid_size}x{args.grid_size}_{args.agent_type}_{args.n_problems}probs'
    
    for _ in range(args.n_agents):
        if(args.agent_type.upper() == "DIPL"):
            from apprentice.agents.cre_agents.cre_agent import CREAgent
            import tutorgym.helpers.ai2t_helpers # Registers SkillApplication -> Action

            agent_args = {
                "function_set": [
                    'ToggleSymbol', 'GetOppositeSymbol', 'OppositeOf', 
                    'Sun', 'Moon', 'CopySymbol', 'Undo'
                ],  # Functions for symbol manipulation
                "feature_set": ['Equals'],  # For comparing cell values
                "planner": 'set_chaining',
                "explanation_choice": "least_operations",
                "search_depth": 2,

                "where_learner": "mostspecific",

                # For STAND
                "when_learner": "decision_tree",
                "which_learner": "when_prediction",
                "action_chooser": "max_which_utility",
                "suggest_uncert_neg": True,

                "error_on_bottom_out": False,

                "extra_features": [],
                "when_args": {
                    "encode_relative": False,  # Disable relative encoding for now to avoid MemSet lookup issues
                    "one_hot": True,
                    "check_sanity": False  # Disable sanity check to avoid decision tree prediction errors
                },
                
                "should_find_neighbors": False,  # Tango uses row/col, not x/y coordinates
                
                # Use Tango fact and action types
                "fact_types": "tango",
                "action_types": "tango",
                "constraints": "tango",
            }

            agent = CREAgent(**agent_args)
        elif(args.agent_type.upper() == "MODULAR"):
            from apprentice.agents.ModularAgent import ModularAgent

            agent_args = dict(
                function_set=[],
                feature_set=['Equals'],
                planner='numba',
                explanation_choice="least_operations",
                search_depth=3,
                when_learner='decisiontree2',
                where_learner="mostspecific",
                state_variablization="metaskill",
                strip_attrs=["to_left", "to_right", "above", "below", "type", "id", "offsetParent", "dom_class"],
                should_find_neighbors=False
            )

            agent = ModularAgent(**agent_args)
        elif(args.agent_type.upper() == "RHS_LHS"):
            from apprentice.agents.RHS_LHS_Agent import RHS_LHS_Agent
            agent = RHS_LHS_Agent(**agent_args)
        else:
            raise ValueError(f"Unrecognized agent type {args.agent_type!r}.")

        run_training(agent, grid_size=args.grid_size, problem_types=args.problem_types, 
                    logger_name=logger_name, n=int(args.n_problems))

