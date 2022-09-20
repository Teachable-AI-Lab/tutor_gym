# from apprentice.agents.ModularAgent import ModularAgent

# from apprentice.agents.pyrete_agent import PyReteAgent
# from apprentice.agents.WhereWhenHowNoFoa import WhereWhenHowNoFoa
from apprentice.working_memory.representation import Sai
# from py_rete import Production
# from py_rete import Fact
# from py_rete import V
# from py_rete.conditions import Filter

from tutorenvs.multicolumn_v import MultiColumnAdditionSymbolic
from tutorenvs.utils import DataShopLogger
from colorama import Back, Fore
import colorama
colorama.init(autoreset=True)

def run_training(agent, logger_name='MulticolumnAddition',  n=10, n_columns=3):

    logger = DataShopLogger(logger_name, extra_kcs=['field'])

    env = MultiColumnAdditionSymbolic(logger=logger, n=n_columns)


    problem_set = [["777", "777"], ["666", "666"], ["777","777"]]
    # problem_set = [["517", "872"], ["925", "461"]]

    env.set_problem(*problem_set[0])

    ALWAYS_UPDATE_STATE = False
    SEND_NEXT_STATE = True

    p = 0
    reward = 1

    while p < n:
        if(reward == 1 or ALWAYS_UPDATE_STATE):
            state = env.get_state()

        response = agent.request(state)

        foci = None
        if response == {}:
            (selection, action, inputs), foci = env.request_demo(return_foci=True)
            sai = Sai(selection=selection, action=action, inputs=inputs)

        elif isinstance(response, Sai):
            sai = response
        else:
            sai = Sai(selection=response['selection'],
                      action=response['action'],
                      inputs=response['inputs'])

        # print('sai', sai.selection, sai.action, sai.inputs)
        reward = env.apply_sai(sai.selection, sai.action, sai.inputs, apply_incorrects=False)
        if(reward == 1):
            if(response == {}):
                print(Back.BLUE + Fore.YELLOW + f"HINT: {sai.selection} -> {sai.inputs}")
            else:
                print(Back.GREEN + Fore.BLACK  + f"CORRECT: {sai.selection} -> {sai.inputs}")
        else:
            print(Back.RED + Fore.BLACK + f"INCORRECT: {sai.selection} -> {sai.inputs}")


        if(SEND_NEXT_STATE and (reward == 1 or ALWAYS_UPDATE_STATE)):
            next_state = env.get_state()
        else:
            next_state = None

        # env.render()
        agent.train(state, sai, int(reward), rhs_id=response.get("rhs_id", None),
                    mapping=response.get("mapping", None),
                     next_state=next_state, foci_of_attention=foci)
                    

        if sai.selection == "done" and reward == 1.0:
            print("+" * 100)
            print(f'Finished problem {p+1} of {n}')
            p += 1
            if(p < len(problem_set)):
                env.set_problem(*problem_set[p])


# @Production(
#     Fact(id=V('selection'), type="TextField", contentEditable=True, value="")
#     & Fact(value=V('value')) & Filter(
#         lambda value: value != "" and is_number(value) and float(value) < 10))
# def update_field(selection, value):
#     return Sai(selection, 'UpdateField', {'value': value})
# 
# 
# def is_number(v):
#     try:
#         float(v)
#         return True
#     except Exception:
#         return False


# @Production(
#     V('f1') << Fact(id=V('id1'), value=V('v1'))
#     & V('f2') << Fact(id=V('id2'), value=V('v2'))
#     & Filter(lambda id1, id2, v1, v2: v1 != "" and is_number(v1) and v2 != ""
#              and is_number(v2) and id1 < id2))
# def add_values(net, f1, f2, id1, id2, v1, v2):
#     if 'depth' not in f1:
#         depth1 = 0
#     else:
#         depth1 = f1['depth']
#     if depth1 > 1:
#         return
# 
#     if 'depth' not in f2:
#         depth2 = 0
#     else:
#         depth2 = f2['depth']
# 
#     if depth1 + depth2 > 1:
#         return
# 
#     print("trying to add values")
#     v1 = float(v1)
#     v2 = float(v2)
#     v3 = v1 + v2
#     if v3 == round(v3):
#         v3 = int(v3)
#     f = Fact(id="({}+{})".format(id1, id2),
#              value=str(v3),
#              depth=max(depth1, depth2) + 1)
#     net.add_fact(f)
# 
# 
# @Production(
#     V('f1') << Fact(id=V('id1'), value=V('v1'))
#     & Filter(lambda id1, v1: v1 != "" and is_number(v1) and float(v1) >= 10))
# def mod10_value(net, f1, id1, v1):
#     if 'depth' not in f1:
#         depth1 = 0
#     else:
#         depth1 = f1['depth']
#     if depth1 > 1:
#         return
# 
#     print("trying to mod10 value")
#     v1 = float(v1)
#     v2 = v1 % 10
#     if v2 == round(v2):
#         v2 = int(v2)
#     f = Fact(id="({}%10)".format(id1), value=str(v2), depth=depth1 + 1)
#     net.add_fact(f)
# 
#     print(net)
# 
# 
# @Production(
#     V('f1') << Fact(id=V('id1'), value=V('v1'))
#     & Filter(lambda id1, v1: v1 != "" and is_number(v1) and float(v1) >= 10))
# def div10_value(net, f1, id1, v1):
#     if 'depth' not in f1:
#         depth1 = 0
#     else:
#         depth1 = f1['depth']
#     if depth1 > 1:
#         return
# 
#     print("trying to div10 value")
#     v1 = float(v1)
#     v2 = v1 // 10
#     if v2 == round(v2):
#         v2 = int(v2)
#     f = Fact(id="({}//10)".format(id1), value=str(v2), depth=depth1 + 1)
#     net.add_fact(f)
# 
#     print(net)


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
    parser.add_argument('--n-problems', default=100, type=int, metavar="<n_problems>",
                        dest="n_problems", help="number of problems")
    parser.add_argument('--n-columns', default=3, type=int, metavar="<n_columns>",
                        dest="n_columns", help="number of columns")
    parser.add_argument('--agent-type', default='DIPL',metavar="<agent_type>",
                        dest="agent_type", help="type of agents DIPL or RHS_LHS")

    args = parser.parse_args(sys.argv[1:])
    # print(args, type(args))
    





    # This
    # agent = RHS_LHS_Agent(**args)
    # run_training(agent, n=100)

    # agent = WhereWhenHowNoFoa('multicolumn', 'multicolumn', search_depth=1)
    # agent = PyReteAgent([update_field, add_values, mod10_value])
    logger_name = f'mc_addition_{args.agent_type}_{args.n_columns}col_{args.n_problems}probs'
    for _ in range(args.n_agents):

        if(args.agent_type.upper() == "DIPL"):
            from apprentice.agents.cre_agents.cre_agent import CREAgent
            agent_args = {
                "search_depth" : 2,
                "where_learner": "antiunify",
                # "where_learner": "mostspecific",
                "when_learner": "sklearndecisiontree",
                # "when_learner": "decisiontree",
                "should_find_neighbors" : True,
                # "which_learner": "nonlinearproportioncorrect",
                # "explanation_choice" : "least_operations",
                "planner" : "setchaining",
                # // "when_args" : {"cross_rhs_inference" : "implicit_negatives"},
                "function_set" : ["Mod10","Div10","Add","Add3"],
                "feature_set" : [],
                "extra_features" : ["SkillCandidates","Match"],
                # "strip_attrs" : ["to_left","to_right","above","below","type","id","offsetParent","dom_class"],
                # "state_variablization" : "metaskill",
                "when_args":{"encode_relative" : True},
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
