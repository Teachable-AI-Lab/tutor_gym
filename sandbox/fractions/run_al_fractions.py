from apprentice.agents.ModularAgent import ModularAgent
from apprentice.agents.WhereWhenHowNoFoa import WhereWhenHowNoFoa
import apprentice
from apprentice.working_memory.representation import Sai
from apprentice.working_memory.numba_operators import *

from tutorenvs.fractions import FractionArithSymbolic

import time

def run_training(agent, n=10):

    env = FractionArithSymbolic()

    p = 0
    c = 0
    while p < n:
        c += 1

        state = env.get_state()
        response = agent.request(state)
        # env.render()

        if response == {}:
            print('hint')
            selection, action, inputs = env.request_demo()
            sai = Sai(selection=selection, action=action, inputs=inputs)

        else:
            sai = Sai(selection=response['selection'],
                      action=response['action'],
                      inputs=response['inputs'])

        print(sai)
        
        reward = env.apply_sai(sai.selection, sai.action, sai.inputs)
        print('reward', reward)

        next_state = env.get_state()
        # print([f'{x["id"]}:{x.get("value",None)}' for x in state.values()])

        agent.train(state, sai, reward, next_state=next_state,#)
                    skill_label="fractions",
                    foci_of_attention=[])

        if sai.selection == "done" and reward == 1.0:
            print('Finished problem {} of {}'.format(p, n))
            p += 1
            
        # if(c > 20):raise ValueError()

        # time.sleep(1)


if __name__ == "__main__":
    function_set = ['RipFloatValue','Add', 'Subtract','Multiply', 'Divide']
    feature_set = ['Equals']

    for i in range(100):
        agent = ModularAgent(
                feature_set=feature_set,
                function_set=function_set,
                planner='numba',
                search_depth=2,
                when_learner='decisiontree',
                where_learner='FastMostSpecific',
                state_variablization='whereswap',
                strip_attrs=["to_left","to_right","above","below","type","id","offsetParent", "dom_class"],
                # when_args= {
                #   "cross_rhs_inference" : "implicit_negatives"
                # }
        )
        # agent = WhereWhenHowNoFoa('fraction arith', 'fraction arith',
        #                       search_depth=1)

        run_training(agent, n=500)
