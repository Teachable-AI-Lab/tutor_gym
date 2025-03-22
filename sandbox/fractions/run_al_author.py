
# from apprentice.working_memory.representation import Sai
# from apprentice.working_memory.numba_operators import *

from tutorgym.env_classes.misc.fraction_arith.fractions import FractionArithmetic
from tutorgym.trainer import Trainer, AuthorTrainer
from tutorgym.evaluator import CompletenessEvaluator
from tutorgym.utils import DataShopLogger
from colorama import Back, Fore
from tutorgym.utils import compare


import colorama
colorama.init(autoreset=True)

import time

# def log_completeness(agent, profile='ground_truth.txt', log=[]):
    
#     log.append(agent.eval_completeness(profile, 
#         print_diff=True, print_correct="when_diff"
#     ))
#     print("---------------")
#     print(agent.process_lrn_mech.grammar)

#     for skill in agent.skills.values():
#         print()
#         print(skill)
#         print(skill.when_lrn_mech)
#     print("---------------")

def resolve_type(typ, logger_name):
    if(typ[:3] == "add"):
        if(logger_name is None): logger_name = "FractionAddition"
        ptypes = ["AD", "AS"]
    elif(typ[:4] == "mult"):
        if(logger_name is None): logger_name = "FractionMult"
        ptypes = ["M"]
    elif(typ[:5] == "arith"):
        # print("ARITH")
        if(logger_name is None): logger_name = "FractionArith"
        ptypes = ["AD","AS","M"]
    else:
        ptypes = typ.split(",")
        if(not all([p in ["AD", "AS", "M"] for p in ptypes])):
            raise ValueError(f"Unrecognized type {typ}")

        if(logger_name is None): logger_name = f"Fraction_{'_'.join(ptypes)}"
    return logger_name, ptypes
        # env = FractionArithSymbolic(logger=logger, problem_types=ptypes, n=n_fracs)


interleaved_problems = [{"op" : "+", "fracs" : [("1","2"), ("1","3")]},
                        {"op" : "+", "fracs" : [("1","4"), ("2","4")]},
                        {"op" : "x", "fracs" : [("4","3"), ("1","2")]},
                        {"op" : "+", "fracs" : [("3","3"), ("2","4")]},
                        {"op" : "+", "fracs" : [("1","5"), ("2","5")]},
                        {"op" : "x", "fracs" : [("2","4"), ("1","3")]}
                        ]

# def make_completeness_profile(env, n=100, name=""):
#     problems = []
#     for i in range(100):
#         env.set_random_problem()
#         problems.append(env.problem)
#     env.make_completeness_profile(problems, name)







def run_training(agent, typ='arith', logger_name=None, n=10, n_fracs=2, demo_args=False):
    logger_name, problem_types = resolve_type(typ, logger_name)
    logger = DataShopLogger(logger_name, extra_kcs=['field'], output_dir='log_al_author')

    env = FractionArithmetic(demo_annotations=["arg_foci", "how_str"],
                             check_annotations=["arg_foci"],
                             problem_types=problem_types, n_fracs=n_fracs)

    # profile = ".frac.compl_prof"
    # if(not os.path.exists(profile)):
    #     env.make_rand_compl_prof() #make_completeness_profile(env, 100, profile)

    compl_evaluator = CompletenessEvaluator(
        eval_freq="problem_end", print_htn=True, print_diff=True,
        check_annotations=[])

    trainer = AuthorTrainer(agent, env, logger=logger,
                problem_set=interleaved_problems, 
                evaluators=[compl_evaluator],
                n_problems=n)
    trainer.start()

    # c_log = []
    # trainer.on_problem_end = lambda : log_completeness(agent, profile, log=c_log)
    

    # for i, obj in enumerate(c_log):
    #     print(f"corr={obj['correctness']*100:2.2f}%, compl={obj['completeness']*100:.2f}%")



if __name__ == "__main__":
    import sys, argparse
    import faulthandler; faulthandler.enable()
    
    parser = argparse.ArgumentParser(
        description='Runs AL agents on fractions')
    parser.add_argument('--n-agents', default=1, type=int, metavar="<n_agents>",
                        dest="n_agents", help="number of agents")
    parser.add_argument('--n-problems', default=20, type=int, metavar="<n_problems>",
                        dest="n_problems", help="number of problems")
    parser.add_argument('--n-fracs', default=2, type=int, metavar="<n_fracs>",
                        dest="n_fracs", help="number of fractions")
    parser.add_argument('--agent-type', default='DIPL',metavar="<agent_type>",
                        dest="agent_type", help="type of agents DIPL or RHS_LHS")
    parser.add_argument('-t', default='arith',metavar="<env_type>",
                        dest="env_type", help="'arith' (i.e. mult & addition), 'mult' or 'addition'")


    args = parser.parse_args(sys.argv[1:])

    print("n_agents", args.n_agents)
    # function_set = ['RipFloatValue','Add','Multiply','Subtract','ConvertNumerator']
                    # 'Divide',
                    # 'DivideRound',
                    #, 'Add3', 'Add4', 'Add5', 
                    #, 'Multiply3', 'Multiply4', 'Multiply5', 
                    # ]
    feature_set = ['Equals']

    
    logger_name = f'frac_{args.env_type}_{args.agent_type}_{args.n_fracs}frac_{args.n_problems}probs'
    
    for _ in range(args.n_agents):
        if(args.agent_type.upper() == "DIPL"):
            from apprentice.agents.cre_agents.cre_agent import CREAgent
            import tutorgym.helpers.ai2t_helpers # Registers SkillApplication -> Action

            agent_args = {
                # "function_set": ['AcrossMultiply','Multiply', 'Add'],
                "function_set": ['Multiply', 'Add'],
                "feature_set": ['Equals'],
                "planner":'set_chaining',
                "explanation_choice" : "least_operations",
                "search_depth": 2,

                # "where_learner" : "antiunify",
                "where_learner": "mostspecific",

                # "when_learner" : 'decisiontree',

                # For STAND
                "when_learner": "stand",
                "which_learner": "when_prediction",
                "action_chooser" : "max_which_utility",
                "suggest_uncert_neg" : True,

                # "when_learner" : 'sklearndecisiontree',
                
                "error_on_bottom_out" : False,
                "one_skill_per_match" : True,
                
                "extra_features" : ["Match"],
                # "when_args" : {"encode_relative" : True, },
                
                "should_find_neighbors" : True,

                "when_args": {
                    "encode_relative" : False,
                    # "one_hot" : True,
                    # "rel_enc_min_sources": 1,
                    "check_sanity" : False
                },

                "process_learner": "htnlearner",
                "track_rollout_preseqs" : True,
                "action_filter_args" : {"thresholds": [0.3, 0, -0.5, -0.75]}
            }

            agent = CREAgent(**agent_args)
        elif(args.agent_type.upper() == "MODULAR"):
            from apprentice.agents.ModularAgent import ModularAgent

            agent_args = dict(
                function_set=['RipFloatValue','Add','Multiply','Subtract','ConvertNumerator'],
                feature_set=['Equals'],
                planner='numba',
                explanation_choice = "least_operations",
                search_depth=3,
                when_learner='decisiontree2',
                # where_learner='FastMostSpecific',
                where_learner="mostspecific",
                # where_learner="version_space",
                # state_variablization='whereswap',
                state_variablization = "metaskill",
                strip_attrs=["to_left","to_right","above","below","type","id","offsetParent", "dom_class"],
                should_find_neighbors=True
            )

            agent = ModularAgent(**agent_args)
        elif(args.agent_type.upper() == "RHS_LHS"):
            from apprentice.agents.RHS_LHS_Agent import RHS_LHS_Agent
            agent = RHS_LHS_Agent(**agent_args)
        else:
            raise ValueError(f"Unrecognized agent type {args.agent_type!r}.")

        run_training(agent, "arith", logger_name=logger_name,  n=int(args.n_problems), n_fracs=args.n_fracs)


    # for i in range(100):
    #     agent = ModularAgent(**agent_args)
    #     # agent = RHS_LHS_Agent(**agent_args)
    #     # agent = WhereWhenHowNoFoa('fraction arith', 'fraction arith',
    #     #                       search_depth=1)

    #     run_training(agent, n=20, demo_args=True)
