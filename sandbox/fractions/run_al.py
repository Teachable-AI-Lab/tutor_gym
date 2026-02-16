from tutorgym.env_classes.apprentice.apprentice_tutor import ApprenticeTutor
from apprentice.agents.ModularAgent import ModularAgent
from apprentice.agents.RHS_LHS_Agent import RHS_LHS_Agent
from apprentice.agents.WhereWhenHowNoFoa import WhereWhenHowNoFoa
import apprentice
from apprentice.working_memory.representation import Sai
# from apprentice.working_memory.numba_operators import *
from tutorgym.envs.apprentice.cognitive_models.logarithms import (
    htn_logarithms_quotient as logarithms_quotient,
    htn_logarithms_product as logarithms_product,
    htn_logarithms_power as logarithms_power,
)
domain_name= "exponents_product" #domain_name= "exponents_power"
scaffold = "all"
# from tutorenvs.fractions_v import FractionArithSymbolic
from tutorgym.env_classes.misc.fraction_arith.fractions import FractionArithmetic
from tutorgym.trainer import Trainer, AuthorTrainer
from tutorgym.utils import DataShopLogger
# from colorama import Back, Fore

# import colorama
# colorama.init(autoreset=True)

import time

from random import choice       # <-- You wanted this included

############################################################
# SIMPLE INTERLEAVE CONTROLLER + EXPONENT PROBLEM SET
############################################################

#class SimpleInterleaveController:
    #def __init__(self, problem_list, max_cycles=1):
        #self.problem_list = problem_list
        #self.index = 0
        #self.max_cycles = max_cycles
        #self.count = 0

    #def __iter__(self):
        #return self

    #def __next__(self):
        #if self.count >= self.max_cycles * len(self.problem_list):
            #raise StopIteration

        #prob = self.problem_list[self.index]
        #self.index = (self.index + 1) % len(self.problem_list)
        #self.count += 1
        #return prob
# ----------------------------------------------------------------------
class BKTTrackingInterleaveController:


    def __init__(self, problem_list, bkt_probs, max_cycles=1, mastery_threshold=0.95):
        self.problem_list = problem_list
        self.index = 0
        self.max_cycles = max_cycles
        self.count = 0

        self.bkt_probs = bkt_probs
        self.mastery_threshold = mastery_threshold

        # Student model: KC -> mastery probability (initialized from "known")
        self.mastery_prob = {kc: bkt_probs[kc]["known"] for kc in bkt_probs}

        # track what problem we are on so update() knows which KCs to update
        self.current_prob = None
        self.steps_updated = set()  # prevents double-updating the same step

    def __iter__(self):
        return self

    def __next__(self):
        if self.count >= self.max_cycles * len(self.problem_list):
            raise StopIteration

        prob = self.problem_list[self.index]
        prob = prob.copy() if isinstance(prob, dict) else prob
        self.index = (self.index + 1) % len(self.problem_list)
        self.count += 1

        self.current_prob = prob
        self.steps_updated = set()
        return prob

    def update(self, step, reward, action_type="ATTEMPT"):
        # only update on attempts (matches the transcript + old BKT controller behavior)
        if action_type != "ATTEMPT":
            return

        # avoid multiple updates for the same step in the same problem
        if step in self.steps_updated:
            return
        self.steps_updated.add(step)

        if self.current_prob is None:
            return

        # binary correctness
        correct = 1 if reward > 0 else 0

        
        step_to_kcs = self.current_prob.get("step_to_kcs", None)

        if step_to_kcs is not None:
            kcs = step_to_kcs.get(step, [])   # safest: unknown steps update nothing
        else:
            kcs = self.current_prob.get("kc_list", [])

        print("BKT UPDATE STEP:", step, "| updating KCs:", kcs)
        for kc in kcs:
            if kc not in self.bkt_probs:
                continue

            guess = self.bkt_probs[kc]["guess"]
            slip  = self.bkt_probs[kc]["slip"]
            learn = self.bkt_probs[kc]["learn"]

            p_known = self.mastery_prob.get(kc, self.bkt_probs[kc]["known"])

            # observation likelihoods (copied logic from the old BKT controller)
            if correct == 1:
                p_obs_not_known = guess
                p_obs_known = 1 - slip
            else:
                p_obs_not_known = 1 - guess
                p_obs_known = slip

            # Bayes update with learning transition
            p_not_learned = (1 - learn) * p_obs_not_known * (1 - p_known)
            p_learned = learn * p_obs_not_known * (1 - p_known) + p_obs_known * p_known

            self.mastery_prob[kc] = p_learned / (p_learned + p_not_learned)

# ------------------------ EXPONENT PROBLEM SET ------------------------

bkt_probs = {
    "power_rule":    {"known": 0.2, "learn": 0.15, "guess": 0.2, "slip": 0.1},
    "product_rule":  {"known": 0.2, "learn": 0.15, "guess": 0.2, "slip": 0.1},
    "quotient_rule": {"known": 0.2, "learn": 0.15, "guess": 0.2, "slip": 0.1},
}

POWER_PROBLEMS = [
    {"domain": "exponents_power", "initial_problem": "(5^3)^4",
     "kc_list": ["power_rule"]},

    {"domain": "exponents_power", "initial_problem": "(2^6)^2",
     "kc_list": ["power_rule"]},

    {"domain": "exponents_power", "initial_problem": "(9^2)^5",
     "kc_list": ["power_rule"]},

    {"domain": "exponents_power", "initial_problem": "(7^4)^3",
     "kc_list": ["power_rule"]},
]

PRODUCT_PROBLEMS = [
    {"domain": "exponents_product", "initial_problem": "5^3 * 5^7",
     "kc_list": ["product_rule"]},

    {"domain": "exponents_product", "initial_problem": "3^8 * 3^2",
     "kc_list": ["product_rule"]},

    {"domain": "exponents_product", "initial_problem": "11^5 * 11^4",
     "kc_list": ["product_rule"]},

    {"domain": "exponents_product", "initial_problem": "6^9 * 6^3",
     "kc_list": ["product_rule"]},
]

QUOTIENT_PROBLEMS = [
    {"domain": "exponents_quotient", "initial_problem": "8^12 / 8^4",
     "kc_list": ["quotient_rule"]},

    {"domain": "exponents_quotient", "initial_problem": "10^9 / 10^3",
     "kc_list": ["quotient_rule"]},

    {"domain": "exponents_quotient", "initial_problem": "4^7 / 4^2",
     "kc_list": ["quotient_rule"]},

    {"domain": "exponents_quotient", "initial_problem": "12^6 / 12^1",
     "kc_list": ["quotient_rule"]},
]
EXPONENT_PROBLEMS = POWER_PROBLEMS + PRODUCT_PROBLEMS + QUOTIENT_PROBLEMS


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
    logger = DataShopLogger(logger_name, extra_kcs=['field'], output_dir='log_al')

    # Use exponents domain
    env = ApprenticeTutor(domain=domain_name, scaffold=scaffold)

    # Attach your custom controller and problem set
    controller = BKTTrackingInterleaveController(
        EXPONENT_PROBLEMS,
        bkt_probs=bkt_probs,
        max_cycles=1
)


    trainer = Trainer(
        agent,
        env,
        logger=logger,
        outer_loop_controller=controller
    )

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
            import tutorgym.helpers.ai2t_helpers # Registers SkillApplication -> Action

            agent_args = {
                # "function_set": ['AcrossMultiply','Multiply', 'Add'],
                #"function_set": ['PowerRule', 'MultiplyExponents'],
                "function_set": ["PowerRule","MultiplyExponents","ProductRule","SimplifyProduct"],
                "feature_set": ['Equals'],
                "planner":'set_chaining',
                "explanation_choice" : "least_operations",
                "search_depth": 2,

                # "where_learner" : "antiunify",
                "where_learner": "mostspecific",

                # For STAND
                "when_learner": "decision_tree",
                "which_learner": "when_prediction",
                "action_chooser" : "max_which_utility",
                "suggest_uncert_neg" : True,

                "error_on_bottom_out" : False,

                # "when_learner" : 'sklearndecisiontree',
                # "when_learner" : 'decisiontree',
                
                "extra_features" : ["Match"],
                "when_args" : {"encode_relative" : True, "one_hot" : True},
                
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
