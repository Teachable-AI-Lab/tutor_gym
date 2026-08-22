
from tutorgym.env_classes.apprentice.apprentice_tutor import ApprenticeTutor
from apprentice.agents.ModularAgent import ModularAgent
from apprentice.agents.RHS_LHS_Agent import RHS_LHS_Agent
from apprentice.agents.WhereWhenHowNoFoa import WhereWhenHowNoFoa
import apprentice
from apprentice.working_memory.representation import Sai
from tutorgym.env_classes.misc.fraction_arith.fractions import FractionArithmetic
from tutorgym.trainer import Trainer, AuthorTrainer
from tutorgym.utils import DataShopLogger
from tutorgym.eval.llm_stu_eval import (
    FRAC_AS_PROBLEMS, FRAC_AD_PROBLEMS, FRAC_M_PROBLEMS, FRAC_ALL_PROBLEMS,
    fraction_bkt_probs,
    SimpleBlockedController, SimpleInterleaveController, BKTTrackingInterleaveController,
    generate_fraction_problem, _KC_TO_PTYPE,
)

import time
from random import choice, shuffle

domain_name = "exponents_product"
scaffold = "all"

############################################################
# LEGACY EXPONENT PROBLEM SET (kept for reference)
############################################################

bkt_probs = {
    "power_rule":    {"known": 0.2, "learn": 0.15, "guess": 0.2, "slip": 0.1},
    "product_rule":  {"known": 0.2, "learn": 0.15, "guess": 0.2, "slip": 0.1},
    "quotient_rule": {"known": 0.2, "learn": 0.15, "guess": 0.2, "slip": 0.1},
}

POWER_PROBLEMS = [
    {"domain": "exponents_power", "initial_problem": "(5^3)^4",
     "kc_list": ["power_rule"],
     "step_to_kcs": {"apply_power_rule": ["power_rule"], "simplify": ["power_rule"], "done": ["power_rule"]}},
    {"domain": "exponents_power", "initial_problem": "(2^6)^2",
     "kc_list": ["power_rule"],
     "step_to_kcs": {"apply_power_rule": ["power_rule"], "simplify": ["power_rule"], "done": ["power_rule"]}},
    {"domain": "exponents_power", "initial_problem": "(9^2)^5",
     "kc_list": ["power_rule"],
     "step_to_kcs": {"apply_power_rule": ["power_rule"], "simplify": ["power_rule"], "done": ["power_rule"]}},
    {"domain": "exponents_power", "initial_problem": "(7^4)^3",
     "kc_list": ["power_rule"],
     "step_to_kcs": {"apply_power_rule": ["power_rule"], "simplify": ["power_rule"], "done": ["power_rule"]}},
]

PRODUCT_PROBLEMS = [
    {"domain": "exponents_product", "initial_problem": "5^3 * 5^7",
     "kc_list": ["product_rule"],
     "step_to_kcs": {"apply_product_rule": ["product_rule"], "simplify": ["product_rule"], "done": ["product_rule"]}},
    {"domain": "exponents_product", "initial_problem": "3^8 * 3^2",
     "kc_list": ["product_rule"],
     "step_to_kcs": {"apply_product_rule": ["product_rule"], "simplify": ["product_rule"], "done": ["product_rule"]}},
    {"domain": "exponents_product", "initial_problem": "11^5 * 11^4",
     "kc_list": ["product_rule"],
     "step_to_kcs": {"apply_product_rule": ["product_rule"], "simplify": ["product_rule"], "done": ["product_rule"]}},
    {"domain": "exponents_product", "initial_problem": "6^9 * 6^3",
     "kc_list": ["product_rule"],
     "step_to_kcs": {"apply_product_rule": ["product_rule"], "simplify": ["product_rule"], "done": ["product_rule"]}},
]

QUOTIENT_PROBLEMS = [
    {"domain": "exponents_quotient", "initial_problem": "8^12 / 8^4",
     "kc_list": ["quotient_rule"],
     "step_to_kcs": {"apply_quotient_rule": ["quotient_rule"], "simplify": ["quotient_rule"], "done": ["quotient_rule"]}},
    {"domain": "exponents_quotient", "initial_problem": "10^9 / 10^3",
     "kc_list": ["quotient_rule"],
     "step_to_kcs": {"apply_quotient_rule": ["quotient_rule"], "simplify": ["quotient_rule"], "done": ["quotient_rule"]}},
    {"domain": "exponents_quotient", "initial_problem": "4^7 / 4^2",
     "kc_list": ["quotient_rule"],
     "step_to_kcs": {"apply_quotient_rule": ["quotient_rule"], "simplify": ["quotient_rule"], "done": ["quotient_rule"]}},
    {"domain": "exponents_quotient", "initial_problem": "12^6 / 12^1",
     "kc_list": ["quotient_rule"],
     "step_to_kcs": {"apply_quotient_rule": ["quotient_rule"], "simplify": ["quotient_rule"], "done": ["quotient_rule"]}},
]

EXPONENT_PROBLEMS = POWER_PROBLEMS + PRODUCT_PROBLEMS + QUOTIENT_PROBLEMS
BLOCKED_PROBLEMS  = POWER_PROBLEMS + PRODUCT_PROBLEMS + QUOTIENT_PROBLEMS
INTERLEAVED_PROBLEMS = [
    POWER_PROBLEMS[0], PRODUCT_PROBLEMS[0], QUOTIENT_PROBLEMS[0],
    POWER_PROBLEMS[1], PRODUCT_PROBLEMS[1], QUOTIENT_PROBLEMS[1],
    POWER_PROBLEMS[2], PRODUCT_PROBLEMS[2], QUOTIENT_PROBLEMS[2],
    POWER_PROBLEMS[3], PRODUCT_PROBLEMS[3], QUOTIENT_PROBLEMS[3],
]


############################################################
# CREAgent config for fractions (no LCM per paper spec)
############################################################

FRAC_CRE_AGENT_ARGS = {
    "function_set": ["Add", "Multiply", "Copy", "AcrossMultiply", "Num"],
    "feature_set": ["Equals"],
    "planner": "set_chaining",
    "explanation_choice": "least_operations",
    "search_depth": 2,
    "where_learner": "mostspecific",
    "when_learner": "decision_tree",
    "which_learner": "when_prediction",
    "action_chooser": "max_which_utility",
    "suggest_uncert_neg": True,
    "error_on_bottom_out": False,
    "extra_features": ["Match"],
    "when_args": {"encode_relative": True, "one_hot": True},
    "should_find_neighbors": True,
}

def make_cre_agent():
    from apprentice.agents.cre_agents.cre_agent import CREAgent
    import tutorgym.helpers.ai2t_helpers
    return CREAgent(**FRAC_CRE_AGENT_ARGS)


############################################################
# AL FRACTIONS RUN FUNCTIONS
############################################################

_FRAC_KCS = list(fraction_bkt_probs.keys())

def run_al_fractions_blocked(max_cycles=1):
    """Blocked: AS block (10), then AD block (14), then M block (24). Within-block order randomized."""
    logger = DataShopLogger("AL_Fractions_Blocked",
                output_dir='stu_eval_logs/al_fractions_blocked',
                extra_kcs=_FRAC_KCS)
    env   = FractionArithmetic()
    agent = make_cre_agent()

    as_block = FRAC_AS_PROBLEMS.copy()
    ad_block = FRAC_AD_PROBLEMS.copy()
    m_block  = FRAC_M_PROBLEMS.copy()
    shuffle(as_block); shuffle(ad_block); shuffle(m_block)

    controller = SimpleBlockedController(as_block + ad_block + m_block, max_cycles=max_cycles)
    trainer = Trainer(agent, env, logger=logger,
                outer_loop_controller=controller,
                num_incorrect_force_demo=2)
    trainer.start()
    print("-- AL FRACTIONS BLOCKED END --")


def run_al_fractions_interleaved(max_cycles=1):
    """Interleaved: fully random ordering of all 48 problems."""
    logger = DataShopLogger("AL_Fractions_Interleaved",
                output_dir='stu_eval_logs/al_fractions_interleaved',
                extra_kcs=_FRAC_KCS)
    env   = FractionArithmetic()
    agent = make_cre_agent()

    all_probs = FRAC_ALL_PROBLEMS.copy()
    shuffle(all_probs)

    controller = SimpleInterleaveController(all_probs, max_cycles=max_cycles)
    trainer = Trainer(agent, env, logger=logger,
                outer_loop_controller=controller,
                num_incorrect_force_demo=2)
    trainer.start()
    print("-- AL FRACTIONS INTERLEAVED END --")


def run_al_fractions_bkt(max_cycles=48):
    """BKT: adaptive selection until all 3 KCs mastered or max_cycles reached."""
    logger = DataShopLogger("AL_Fractions_BKT",
                output_dir='stu_eval_logs/al_fractions_bkt',
                extra_kcs=_FRAC_KCS)
    env   = FractionArithmetic()
    agent = make_cre_agent()

    controller = BKTTrackingInterleaveController(
        [],
        bkt_probs=fraction_bkt_probs,
        max_cycles=max_cycles,
        mastery_threshold=0.8,
        problem_generator=generate_fraction_problem,
        kc_to_ptype=_KC_TO_PTYPE,
    )
    trainer = Trainer(agent, env, logger=logger,
                outer_loop_controller=controller,
                num_incorrect_force_demo=2)
    trainer.start()
    print("-- AL FRACTIONS BKT END --")


############################################################
# LEGACY run_training (exponents, kept for reference)
############################################################

def resolve_type(typ, logger_name):
    if(typ[:3] == "add"):
        if(logger_name is None): logger_name = "FractionAddition"
        ptypes = ["AD", "AS"]
    elif(typ[:4] == "mult"):
        if(logger_name is None): logger_name = "FractionMult"
        ptypes = ["M"]
    elif(typ[:5] == "arith"):
        if(logger_name is None): logger_name = "FractionArith"
        ptypes = ["AD","AS","M"]
    else:
        ptypes = typ.split(",")
        if(not all([p in ["AD", "AS", "M"] for p in ptypes])):
            raise ValueError(f"Unrecognized type {typ}")
        if(logger_name is None): logger_name = f"Fraction_{'_'.join(ptypes)}"
    return logger_name, ptypes

def run_training(agent, typ='arith', logger_name=None, n=10, n_fracs=2, demo_args=False):
    logger_name, problem_types = resolve_type(typ, logger_name)
    logger = DataShopLogger(logger_name, extra_kcs=['field'], output_dir='log_al')
    env = ApprenticeTutor(domain=domain_name, scaffold=scaffold)
    controller = BKTTrackingInterleaveController(
        EXPONENT_PROBLEMS, bkt_probs=bkt_probs, max_cycles=20, mastery_threshold=0.95)
    trainer = Trainer(agent, env, logger=logger, outer_loop_controller=controller)
    trainer.start()


############################################################
# MAIN
############################################################

if __name__ == "__main__":
    import sys, argparse
    import faulthandler; faulthandler.enable()

    parser = argparse.ArgumentParser(description='Run AL agent on fractions experiment')
    parser.add_argument('--condition', type=str, default="blocked",
                        choices=['blocked', 'interleaved', 'bkt'],
                        help='Which condition to run')
    parser.add_argument('--n-agents', default=1, type=int, dest="n_agents",
                        help='Number of independent AL agents to run')
    parser.add_argument('--max-cycles', default=None, type=int, dest="max_cycles",
                        help='Max cycles through problem set (or max problems for bkt; defaults to 1 for blocked/interleaved, 48 for bkt)')

    args = parser.parse_args(sys.argv[1:])

    print(f"Running fractions/{args.condition} with {args.n_agents} AL agent(s)")

    for i in range(args.n_agents):
        print(f"\n--- Agent {i+1}/{args.n_agents} ---")
        if args.condition == "blocked":
            run_al_fractions_blocked(max_cycles=args.max_cycles if args.max_cycles is not None else 1)
        elif args.condition == "interleaved":
            run_al_fractions_interleaved(max_cycles=args.max_cycles if args.max_cycles is not None else 1)
        elif args.condition == "bkt":
            run_al_fractions_bkt(max_cycles=args.max_cycles if args.max_cycles is not None else 48)
