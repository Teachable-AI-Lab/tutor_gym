from apprentice.agents.ModularAgent import ModularAgent
from apprentice.agents.RHS_LHS_Agent import RHS_LHS_Agent
from apprentice.agents.WhereWhenHowNoFoa import WhereWhenHowNoFoa
import apprentice
from apprentice.working_memory.representation import Sai
# from apprentice.working_memory.numba_operators import *

from tutorenvs.fractions_v import FractionArithSymbolic
from tutorenvs.fractions_std import FractionArithmetic
from tutorenvs.trainer import Trainer
from tutorenvs.utils import DataShopLogger
from colorama import Back, Fore
from tutorenvs.utils import compare

import colorama
colorama.init(autoreset=True)

import time

# def run_training(agent, typ='arith', logger_name=None, n=10, n_fracs=3, demo_args=False):
#     logger = DataShopLogger(logger_name, extra_kcs=['field'])


#     if(typ[:3] == "add"):
#         if(logger_name is None): logger_name = "FractionAddition"
#         env = FractionArithSymbolic(logger=logger, problem_types=["AD","AS"], n=n_fracs)
#     elif(typ[:4] == "mult"):
#         if(logger_name is None): logger_name = "FractionMult"
#         env = FractionArithSymbolic(logger=logger, problem_types=["M"], n=n_fracs)
#     elif(typ[:5] == "arith"):
#         # print("ARITH")
#         if(logger_name is None): logger_name = "FractionArith"
#         env = FractionArithSymbolic(logger=logger, problem_types=["AD","AS","M"], n=n_fracs)
#     else:
#         ptypes = typ.split(",")
#         if(not all([p in ["AD", "AS", "M"] for p in ptypes])):
#             raise ValueError(f"Unrecognized type {typ}")

#         if(logger_name is None): logger_name = f"Fraction_{'_'.join(ptypes)}"
#         env = FractionArithSymbolic(logger=logger, problem_types=ptypes, n=n_fracs)

#     ALWAYS_UPDATE_STATE = False
#     SEND_NEXT_STATE = True

#     p = 0
#     reward = 1
#     # c = 0
#     while p < n:
#         # c += 1
#         if(reward == 1 or ALWAYS_UPDATE_STATE):
#             state = env.get_state()

#         response = agent.request(state)

#         foci = None
#         if response == {}:
#             # print('hint')
#             (selection, action, inputs), foci = env.request_demo(return_foci=True)
#             sai = Sai(selection=selection, action=action, inputs=inputs)

#         elif isinstance(response, Sai):
#             sai = response
#         else:
#             sai = Sai(selection=response['selection'],
#                       action=response['action'],
#                       inputs=response['inputs'])

#         # print(sai)
        
#         reward = env.apply_sai(sai.selection, sai.action, sai.inputs)
        

#         # print("<<", reward, foci)

#         if(SEND_NEXT_STATE and (reward == 1 or ALWAYS_UPDATE_STATE)):
#             next_state = env.get_state()
#         else:
#             next_state = None
#         # next_state = env.get_state()
#         # print([f'{x["id"]}:{x.get("value",None)}' for x in state.values()])

#         agent.train(state, sai, int(reward),
#                     rhs_id=response.get("rhs_id", None),
#                     mapping=response.get("mapping", None),
#                     next_state=next_state,
#                     # skill_label="fractions",
#                     foci_of_attention=foci)

#         if(reward == 1):
#             if(response == {}):
#                 print(Back.BLUE + Fore.YELLOW + f"HINT: {sai.selection} -> {sai.inputs}")
#             else:
#                 print(Back.GREEN + Fore.BLACK  + f"CORRECT: {sai.selection} -> {sai.inputs}")
#         else:
#             print(Back.RED + Fore.BLACK + f"INCORRECT: {sai.selection} -> {sai.inputs}")

#         if sai.selection == "done" and reward == 1.0:
#             print('Finished problem {} of {}'.format(p, n))
#             p += 1
            
#         # if(c > 20):raise ValueError()

#         # time.sleep(1)

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

def run_training(agent, typ='arith', logger_name=None, n=10, n_fracs=2, demo_args=False):
    logger_name, problem_types = resolve_type(typ, logger_name)
    logger = DataShopLogger(logger_name, extra_kcs=['field'], output_dir='log_al_norf')
    env = FractionArithmetic(problem_types=problem_types, n_fracs=n_fracs,
                             demo_args=False, check_args=False)
    trainer = Trainer(agent, env, logger=logger, n_problems=n)
    trainer.start()

if __name__ == "__main__":
    import sys, argparse
    import faulthandler; faulthandler.enable()
    
    parser = argparse.ArgumentParser(
        description='Runs AL agents on multi-column addition')
    parser.add_argument('--n-agents', default=50, type=int, metavar="<n_agents>",
                        dest="n_agents", help="number of agents")
    parser.add_argument('--n-problems', default=500, type=int, metavar="<n_problems>",
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

            agent_args = {
                "function_set": ['Add','Multiply'],#'ConvertNumerator'],
                # "feature_set": [],
                "feature_set": ['Equals'],
                "planner":'set_chaining',
                "explanation_choice" : "least_operations",
                "search_depth": 2,

                # "where_learner" : "antiunify",
                "where_learner": "mostspecific",

                # For STAND
                # "when_learner": "stand",
                # "which_learner": "when_prediction",
                # "action_chooser" : "max_which_utility",
                # "suggest_uncert_neg" : True,

                "when_learner" : 'sklearndecisiontree',
                # "when_learner" : 'decisiontree',
                
                "extra_features" : ["Match"],#, "SkillCandidates"],
                "when_args" : {"encode_relative" : False},
                
                "should_find_neighbors" : True
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

        run_training(agent, args.env_type, logger_name=logger_name,  n=int(args.n_problems), n_fracs=args.n_fracs)


    # for i in range(100):
    #     agent = ModularAgent(**agent_args)
    #     # agent = RHS_LHS_Agent(**agent_args)
    #     # agent = WhereWhenHowNoFoa('fraction arith', 'fraction arith',
    #     #                       search_depth=1)

    #     run_training(agent, n=20, demo_args=True)
