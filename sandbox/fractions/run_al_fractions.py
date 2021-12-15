from apprentice.agents.ModularAgent import ModularAgent
from apprentice.agents.RHS_LHS_Agent import RHS_LHS_Agent
from apprentice.agents.WhereWhenHowNoFoa import WhereWhenHowNoFoa
import apprentice
from apprentice.working_memory.representation import Sai
from apprentice.working_memory.numba_operators import *

from tutorenvs.fractions_v import FractionArithSymbolic
from tutorenvs.utils import DataShopLogger
from colorama import Back, Fore
from tutorenvs.utils import compare



import time

def run_training(agent, logger_name='FractionAddition', n=10, n_fracs=3, use_foci=False):
    logger = DataShopLogger(logger_name, extra_kcs=['field'])

    env = FractionArithSymbolic(logger=logger, n=n_fracs)
    ALWAYS_UPDATE_STATE = False
    SEND_NEXT_STATE = True

    p = 0
    reward = 1
    # c = 0
    while p < n:
        # c += 1
        if(reward == 1 or ALWAYS_UPDATE_STATE):
            state = env.get_state()

        response = agent.request(state)

        foci = None
        if response == {}:
            print('hint')
            (selection, action, inputs), foci = env.request_demo(return_foci=True)
            sai = Sai(selection=selection, action=action, inputs=inputs)

        elif isinstance(response, Sai):
            sai = response
        else:
            sai = Sai(selection=response['selection'],
                      action=response['action'],
                      inputs=response['inputs'])

        print(sai)
        
        reward = env.apply_sai(sai.selection, sai.action, sai.inputs)
        if(reward == 1):
            if(response == {}):
                print(Back.BLUE + Fore.YELLOW + f"HINT: {sai.selection} -> {sai.inputs}")
            else:
                print(Back.GREEN + Fore.BLACK  + f"CORRECT: {sai.selection} -> {sai.inputs}")
        else:
            print(Back.RED + Fore.BLACK + f"INCORRECT: {sai.selection} -> {sai.inputs}")

        print("<<", reward, foci)

        if(SEND_NEXT_STATE and (reward == 1 or ALWAYS_UPDATE_STATE)):
            next_state = env.get_state()
        else:
            next_state = None
        # next_state = env.get_state()
        # print([f'{x["id"]}:{x.get("value",None)}' for x in state.values()])

        agent.train(state, sai, int(reward),
                    rhs_id=response.get("rhs_id", None),
                    mapping=response.get("mapping", None),
                    next_state=next_state,
                    # skill_label="fractions",
                    foci_of_attention=foci)

        if sai.selection == "done" and reward == 1.0:
            print('Finished problem {} of {}'.format(p, n))
            p += 1
            
        # if(c > 20):raise ValueError()

        # time.sleep(1)


if __name__ == "__main__":
    import sys, argparse
    parser = argparse.ArgumentParser(
        description='Runs AL agents on multi-column addition')
    parser.add_argument('--n-agents', default=50, type=int, metavar="<n_agents>",
                        dest="n_agents", help="number of agents")
    parser.add_argument('--n-problems', default=100, type=int, metavar="<n_problems>",
                        dest="n_problems", help="number of problems")
    parser.add_argument('--n-fracs', default=3, type=int, metavar="<n_fracs>",
                        dest="n_fracs", help="number of fractions")
    parser.add_argument('--agent-type', default='DIPL',metavar="<agent_type>",
                        dest="agent_type", help="type of agents DIPL or RHS_LHS")

    args = parser.parse_args(sys.argv[1:])


    function_set = ['RipFloatValue',
                    'Add',
                    'Multiply',
                    'Subtract',
                    'ConvertNumerator',
                    # 'Divide',
                    # 'DivideRound',
                    #, 'Add3', 'Add4', 'Add5', 
                    #, 'Multiply3', 'Multiply4', 'Multiply5', 
                    ]
    feature_set = ['Equals']

    agent_args = dict(
            feature_set=feature_set,
            function_set=function_set,
            planner='numba',
            explanation_choice = "least_operations",
            search_depth=3,
            when_learner='decisiontree2',
            # where_learner='FastMostSpecific',
            where_learner="version_space",
            # state_variablization='whereswap',
            state_variablization = "metaskill",
            strip_attrs=["to_left","to_right","above","below","type","id","offsetParent", "dom_class"]
                )

    logger_name = f'frac_addition_{args.agent_type}_{args.n_fracs}frac_{args.n_problems}probs'
    for _ in range(args.n_agents):
        if(args.agent_type.upper() == "DIPL"):
            agent = ModularAgent(**agent_args)
        elif(args.agent_type.upper() == "RHS_LHS"):
            agent = RHS_LHS_Agent(**agent_args)
        else:
            raise ValueError(f"Unrecognized agent type {args.agent_type!r}.")

        run_training(agent, logger_name=logger_name,  n=int(args.n_problems), n_fracs=args.n_fracs)


    # for i in range(100):
    #     agent = ModularAgent(**agent_args)
    #     # agent = RHS_LHS_Agent(**agent_args)
    #     # agent = WhereWhenHowNoFoa('fraction arith', 'fraction arith',
    #     #                       search_depth=1)

    #     run_training(agent, n=20, use_foci=True)
