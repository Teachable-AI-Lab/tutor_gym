from tutorgym.env_classes.misc.mc_addition.multicolumn import MultiColumnAddition, Action, ProblemState
from tutorgym.trainer import Trainer, AuthorTrainer
from tutorgym.evaluator import CompletenessEvaluator
from tutorgym.utils import DataShopLogger
from colorama import Back, Fore
from tutorgym.utils import compare

from colorama import Back, Fore
import colorama
from pprint import pprint
import json
colorama.init(autoreset=True)



def log_completeness(agent, profile='ground_truth.txt', log=[]):
    print(agent.process_lrn_mech.grammar)
    log.append(agent.eval_completeness(profile, 
        print_diff=True, print_correct="when_diff"
    ))
    print("---------------")
    for skill in agent.skills.values():
        print()
        print(skill)
        print(skill.when_lrn_mech)
    print("---------------")



edge_case_set = [
    ["777", "777"],
    ["773", "773"],
    ["737", "737"],
    ["377", "377"],
    ["337", "337"],
    ["733", "733"], # missing in CHI2020
    ["333", "333"], # missing in CHI2020
    ["999", "001"],
    ["999", "010"],
    ["999", "100"],
    ["999", "111"],
    ["999", "011"],
    ["999", "110"],
    ["999", "101"],
]

old_training_set = [
    ["534", "698"], #0 
    # ["872", "371"], #1 
    ["839", "445"], #2  
    ["287", "134"], #3
    ["643", "534"], #4
    ["248", "137"], #5
    ["234", "142"], #6
    ["539", "461"], #7
    # ["433", "576"], #8
    # ["764", "335"], #9
    # ["533", "698"], #10
]

training_set = [
    ["574", "798"],
    ["248", "315"],
    ["252", "533"],
    ["394", "452"],
    ["872", "371"],
    ["334", "943"],
    ["189", "542"],
]


extra = [
    # ["777", "777"],
    # ["999", "101"],
    # ["999", "111"],
    # ["999", "001"],
]

start_probs = [
    ["534", "698"],
    ["234", "127"],
    # ["42", "7"],
    # ["2", "9"],
    # ["674", "9"],
]


ground_truth_set = training_set + edge_case_set

# --------------------------
# : Creating completeness profiles


# def make_completeness_profile(env, problems, output_file):
#     with open(output_file, 'w') as profile:
#         for prob_args in problems:
#             env.set_problem(*prob_args)
#             next_states = [env.get_state()]

#             covered_states = set()
#             while(len(next_states) > 0):
#                 new_states = []
#                 for state in next_states:
#                     ps = ProblemState(state)
#                     if(ps in covered_states):
#                         continue
#                     else:
#                         covered_states.add(ps)

#                     env.set_state(state)
#                     demos = env.get_all_demos(state)
#                     sais = [d.sai.get_info() for d in demos]
#                     profile.write(json.dumps({'state' : state, 'sais' : sais})+"\n")

#                     for d in demos:
#                         ns = env.apply(d)
#                         new_states.append(ns)
#                         env.set_state(state)
#                 next_states = new_states

def make_completeness_profile(env, n=100, name=""):
    problems = []
    for i in range(n):
        env.set_random_problem()
        problems.append(env.problem)
    env.make_completeness_profile(problems, name)


def run_training(agent, logger_name='MulticolumnAddition', n=10,
                 n_columns=3, author_train=True, carry_zero=False, random_n_digits=False):
    
    logger = DataShopLogger(logger_name, extra_kcs=['field'])
    problem_set = training_set #+ extra + training_set   #[["777", "777"], ["666", "666"], ["777","777"]]

    # if(author_train):

    print("CARRY ZERO:", carry_zero)
    env = MultiColumnAddition(check_how=False, check_args=True,
            demo_args=True, demo_how=True, n_digits=n_columns,
            carry_zero=carry_zero, random_n_digits=random_n_digits)

    # Randomly generate new completeness profile from env
    profile = f"mc-{'cZ-' if carry_zero else ''}-{n_columns}.txt"
    make_completeness_profile(env, 20, profile)
    

    # env.make_completeness_profile(training_set+edge_case_set, 'exp_z_ground_truth.txt')
    trainer = AuthorTrainer(agent, env, logger=logger, 
                problem_set=problem_set,
                n_problems=20)
                # problem_set=problem_set)#, n_problems=n)
    c_log = []
    # profile = "exp_z_ground_truth.txt" if carry_zero else "ground_truth.txt"

    # TEST SET LOGGING
    # profile = "gt-carryZ-3.txt"
    trainer.on_problem_end = lambda : log_completeness(agent, profile, log=c_log)

    # else:
    #     env = MultiColumnAddition(check_how=False, check_args=False, demo_args=True, demo_how=True, n_digits=n_columns)
    #     trainer = Trainer(agent, env, logger=logger, problem_set=problem_set, n_problems=n)
    trainer.start()

    for i, obj in enumerate(c_log):
        print(f"corr={obj['correctness']*100:2.2f}%, compl={obj['completeness']*100:.2f}%")

if __name__ == "__main__":
    import faulthandler; faulthandler.enable()

    import numpy as np
    np.set_printoptions(edgeitems=30, linewidth=100000, 
        formatter=dict(float=lambda x: "%.3g" % x))
    
    import sys, argparse
    parser = argparse.ArgumentParser(
        description='Runs AL agents on multi-column addition')
    parser.add_argument('--n-agents', default=1, type=int, metavar="<n_agents>",
                        dest="n_agents", help="number of agents")
    parser.add_argument('--n-problems', default=5, type=int, metavar="<n_problems>",
                        dest="n_problems", help="number of problems")
    parser.add_argument('--n-columns', default=3, type=int, metavar="<n_columns>",
                        dest="n_columns", help="number of columns")
    parser.add_argument('--agent-type', default='DIPL',metavar="<agent_type>",
                        dest="agent_type", help="type of agents DIPL or RHS_LHS")

    args = parser.parse_args(sys.argv[1:])

    logger_name = f'mc_addition_{args.agent_type}_{args.n_columns}col_{args.n_problems}probs'
    for _ in range(args.n_agents):

        if(args.agent_type.upper() == "DIPL"):
            from apprentice.agents.cre_agents.cre_agent import CREAgent
            agent_args = {
                "search_depth" : 2,
                # "where_learner": "generalize",
                "where_learner": "mostspecific",

                # "when_learner": "sklearndecisiontree",
                # "when_learner": "decisiontree",
                                
                # For STAND
                "when_learner": "stand",
                "which_learner": "when_prediction",
                "action_chooser" : "max_which_utility",
                "suggest_uncert_neg" : True,

                # "when_args" : {},
                # "when_args" : {},

                # "explanation_choice" : "least_operations",
                "planner" : "setchaining",
                # // "when_args" : {"cross_rhs_inference" : "implicit_negatives"},
                "function_set" : ["OnesDigit","TensDigit","Add","Add3"],
                # "feature_set" : [],
                # "feature_set" : ['Equals'],
                "extra_features" : ["RemoveAll", "SkillCandidates","Match"],
                # "extra_features" : ["SkillValue"],#,"Match"],
                "find_neighbors" : True,
                # "strip_attrs" : ["to_left","to_right","above","below","type","id","offsetParent","dom_class"],
                # "state_variablization" : "metaskill",
                "when_args": {
                    "encode_relative" : True,
                    # "rel_enc_min_sources": 1,
                    "check_sanity" : False
                },

                "process_learner": "htnlearner",
                "track_rollout_preseqs" : True,
                "action_filter_args" : {"thresholds": [.3, 0, -.5, -.75]},

                "implicit_reward_kinds" : ["unordered_groups"]
            }
            agent = CREAgent(**agent_args)
        elif(args.agent_type.upper() == "MODULAR"):
            agent_args = {
                "search_depth" : 3,
                "where_learner": "version_space",
                # "where_learner": "mostspecific",
                "when_learner": "decisiontree2",
                # "when_args" : {""},
                # "which_learner": "nonlinearproportioncorrect",
                "explanation_choice" : "least_operations",
                "planner" : "numba",
                # // "when_args" : {"cross_rhs_inference" : "implicit_negatives"},
                "function_set" : ["RipFloatValue","Mod10","Div10","Add","Add3"],
                "feature_set" : [],
                "strip_attrs" : ["to_left","to_right","above","below","type","id","offsetParent","dom_class"],
                "state_variablization" : "metaskill",
                # "state_variablization" : "whereappend",
                "should_find_neighbors": True
            }

            from apprentice.agents.ModularAgent import ModularAgent
            agent = ModularAgent(**agent_args)
        elif(args.agent_type.upper() == "RHS_LHS"):
            from apprentice.agents.RHS_LHS_Agent import RHS_LHS_Agent
            agent = RHS_LHS_Agent(**agent_args)
        else:
            raise ValueError(f"Unrecognized agent type {args.agent_type!r}.")

        run_training(agent, logger_name=logger_name,  n=int(args.n_problems), n_columns=args.n_columns)







