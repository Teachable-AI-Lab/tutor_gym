from apprentice.agents.ModularAgent import ModularAgent
from apprentice.agents.RHS_LHS_Agent import RHS_LHS_Agent
# from apprentice.agents.pyrete_agent import PyReteAgent
# from apprentice.agents.WhereWhenHowNoFoa import WhereWhenHowNoFoa
from apprentice.working_memory.representation import Sai
# from py_rete import Production
# from py_rete import Fact
# from py_rete import V
# from py_rete.conditions import Filter

from tutorenvs.multicolumn_v import MultiColumnAdditionSymbolic
from colorama import Back, Fore

def run_training(agent, n=10):

    env = MultiColumnAdditionSymbolic(n=8)
    ALWAYS_UPDATE_STATE = False
    SEND_NEXT_STATE = True

    p = 0
    reward = 1

    while p < n:
        if(reward == 1 or ALWAYS_UPDATE_STATE):
            state = env.get_state()

        response = agent.request(state)

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
            print(f'Finished problem {p} of {n}')
            p += 1


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
    args = {
        "search_depth" : 3,
        "where_learner": "version_space",
        "when_learner": "decisiontree2",
        "which_learner": "nonlinearproportioncorrect",
        "explanation_choice" : "least_operations",
        "planner" : "numba",
        # // "when_args" : {"cross_rhs_inference" : "implicit_negatives"},
        "function_set" : ["RipFloatValue","Mod10","Div10","Add","Add3"],
        "feature_set" : [],
        "strip_attrs" : ["to_left","to_right","above","below","type","id","offsetParent","dom_class"],
        "state_variablization" : "metaskill",
        # "function_set" : ["RipFloatValue","Add","Add3", "Mod10","Div10"],
        # "feature_set": [],
        # "planner": "numba",
        # "planner_args" : {

        # },
        # "explanation_choice" : "least_operations",
        # "search_depth": 3,
        # "when_learner": "decisiontree",
        # "where_learner": "VersionSpace",
        # "state_variablization": "metaskill",
        # "strip_attrs" : ["to_left","to_right","above","below","type","id","offsetParent","dom_class"],
        # "when_args": {
        #     "cross_rhs_inference": "none"
        # },
        # "which_learner": "proportioncorrect",
        #     "which_args": {
        #         "remove_utility_type" : "nonlinearproportioncorrect"
        #     },
        # # "which_args": {
        # #     "remove_utility_type": "nonlinearproportioncorrect"
        # # }

    }

    # This
    # agent = RHS_LHS_Agent(**args)
    # run_training(agent, n=100)

    # agent = WhereWhenHowNoFoa('multicolumn', 'multicolumn', search_depth=1)
    # agent = PyReteAgent([update_field, add_values, mod10_value])

    agent = ModularAgent(**args)
    run_training(agent, n=50)
