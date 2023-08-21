# from apprentice.agents.ModularAgent import ModularAgent

# from apprentice.agents.pyrete_agent import PyReteAgent
# from apprentice.agents.WhereWhenHowNoFoa import WhereWhenHowNoFoa
# from apprentice.working_memory.representation import Sai
# from py_rete import Production
# from py_rete import Fact
# from py_rete import V
# from py_rete.conditions import Filter

# from tutorenvs.multicolumn_v import MultiColumnAdditionSymbolic
from tutorenvs.multicolumn_std import MultiColumnAddition
from tutorenvs.utils import DataShopLogger
from tutorenvs.trainer import Trainer
from colorama import Back, Fore
import colorama
from pprint import pprint
colorama.init(autoreset=True)

# def run_training(agent, logger_name='MulticolumnAddition', n=10, n_columns=3, train_conflict_set=False):

#     logger = DataShopLogger(logger_name, extra_kcs=['field'])

#     env = MultiColumnAdditionSymbolic(logger=logger, n=n_columns)


#     problem_set = [["777", "777"], ["666", "666"], ["777","777"]]
#     # problem_set = [["517", "872"], ["925", "461"]]

#     env.set_problem(*problem_set[0])

#     ALWAYS_UPDATE_STATE = False
#     SEND_NEXT_STATE = True

#     p = 0
#     reward = 1
#     total_incorrect = 0
#     total_correct = 0
#     total_hints = 0
#     assistance_records = []
#     is_start_state = True

#     while p < n:
#         if(reward == 1 or ALWAYS_UPDATE_STATE):
#             state = env.get_state()

#         if(p == 50 and is_start_state):
#             print("--DID THIS--")
#             agent.gen_completeness_profile([state], 'comp_prof.txt')
            

#         # print("STATE ACT")
#         # pprint({sel:(x.get('value',None),x.get('locked',None)) for sel, x in state.items()})
#         if(train_conflict_set):
#             # TODO: Env isn't ready for this just yet
#             # agent.act_rollout(state)
#             sais = agent.act_all(state)
#             no_action = sais is None or len(sais) == 0

#             if(no_action):
#                 sai, arg_foci = env.request_demo(return_foci=True)
#                 train_set = [{"state":state, "sai": sai, "arg_foci": arg_foci, "reward" : 1}]
#             else:
#                 train_set = []
#                 for sai in sais:
#                     reward = env.apply_sai(sai[0], sai[1], sai[2], apply_incorrects=False)
#                     train_set.append([{"state":state, "sai": sai, "reward" : reward}])
#                 sai = sais[0]


#             # raise ValueError("DONE")
#         else:
#             sai = agent.act(state)
#             no_action = False if sai else True

#             arg_foci = None
#             if no_action:
#                 sai, arg_foci = env.request_demo(return_foci=True)
#             elif(hasattr(sai, 'as_tuple')):
#                 sai = sai.as_tuple()
                
#             reward = env.apply_sai(sai[0], sai[1], sai[2], apply_incorrects=False)

#             # if(SEND_NEXT_STATE and (reward == 1 or ALWAYS_UPDATE_STATE)):
#             #     next_state = env.get_state()
#             # else:
#             #     next_state = None

#             agent.train(state, sai, int(reward), arg_foci=arg_foci)

#         was_assistance = True
#         if(reward == 1):
#             if(no_action):
#                 total_hints += 1
#                 print(Back.BLUE + Fore.YELLOW + f"HINT: {sai[0]} -> {sai[2]}")
#             else:
#                 total_correct += 1
#                 was_assistance = False
#                 print(Back.GREEN + Fore.BLACK  + f"CORRECT: {sai[0]} -> {sai[2]}")
#         else:
#             total_incorrect += 1
#             print(Back.RED + Fore.BLACK + f"INCORRECT: {sai[0]} -> {sai[2]}")
                    
#         if(was_assistance):
#             assistance_records.append(f'P{p}_{sai[0]}')

#         if sai[0] == "done" and reward == 1.0:
#             print("+" * 100)
#             print(f'Finished problem {p+1} of {n}')
            
#             p += 1
#             if(p < len(problem_set)):
#                 env.set_problem(*problem_set[p])
#             is_start_state = True
#         else:
#             is_start_state = False

#     total = (total_hints+total_incorrect+total_correct)
#     print(f'TOTALS  (correct:{total_correct}, incorrect:{total_incorrect}, hint:{total_hints}, assistance:{total_hints+total_incorrect})')
#     print(f'PERCENTS(correct:{100*(total_correct)/total:.2f}%, incorrect:{100*(total_incorrect)/total:.2f}%, hint:{100*(total_hints)/total:.2f}%, assistance:{100*(total_hints+total_incorrect)/total:.2f}%)')
#     print(f'Last 5 assistance', assistance_records[-5:])

def run_training(agent, logger_name='MulticolumnAddition', n=10,
                 n_columns=3, author_train=True, carry_zero=False):
    
    logger = DataShopLogger(logger_name, extra_kcs=['field'], output_dir='log_al')
    env = MultiColumnAddition(
            demo_args=True, demo_how=False, n_digits=n_columns,
            carry_zero=carry_zero)

    trainer = Trainer(agent, env, logger=logger, n_problems=n)
    trainer.start()


if __name__ == "__main__":
    import faulthandler; faulthandler.enable()

    import numpy as np
    np.set_printoptions(edgeitems=30, linewidth=100000, 
        formatter=dict(float=lambda x: "%.3g" % x))

    
    import sys, argparse
    parser = argparse.ArgumentParser(
        description='Runs AL agents on multi-column addition')
    parser.add_argument('--n-agents', default=50, type=int, metavar="<n_agents>",
                        dest="n_agents", help="number of agents")
    parser.add_argument('--n-problems', default=500, type=int, metavar="<n_problems>",
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
                # "where_learner": "antiunify",
                "where_learner": "mostspecific",
                "when_learner": "sklearndecisiontree",
                # "when_learner": "decisiontree",
                                
                # For STAND
                # "when_learner": "stand",
                # "which_learner": "when_prediction",
                # "action_chooser" : "max_which_utility",
                # "suggest_uncert_neg" : True,

                # "explanation_choice" : "least_operations",
                "planner" : "setchaining",
                # // "when_args" : {"cross_rhs_inference" : "implicit_negatives"},
                "function_set" : ["OnesDigit","TensDigit","Add3", "Add"],
                "feature_set" : [],
                # "feature_set" : ['Equals'],
                "extra_features" : ["SkillCandidates","Match"],
                "find_neighbors" : True,
                # "strip_attrs" : ["to_left","to_right","above","below","type","id","offsetParent","dom_class"],
                # "state_variablization" : "metaskill",
                "when_args": {"encode_relative" : True},
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
