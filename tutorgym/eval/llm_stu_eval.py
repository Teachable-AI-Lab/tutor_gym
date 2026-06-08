from abc import ABC, abstractmethod
from urllib import response
from tutorgym.trainer import AuthorTrainer, Trainer
from tutorgym.utils import DataShopLogger
from tutorgym.agents.oracle_agent import RandomOracleAgent, OracleAgent
from tutorgym.agents.agent_api import AbstactAgent
from tutorgym.env_classes.CTAT.CTAT_tutor import CTAT_Tutor
from tutorgym.env_classes.apprentice.apprentice_tutor import ApprenticeTutor
from tutorgym.env_classes.oatutor.oa_tutors import OATutor
from tutorgym.shared import Action
from pathlib import Path
import requests
import yaml
import time
import traceback
import sys
from colorama import Back, Fore, Style
import argparse
from random import choice, shuffle

from tutorgym.env_classes.misc.fraction_arith.fractions import FractionArithmetic
from tutorgym.eval.llm_base import LLMPromptable, print_response

############################################################
# CONTROLLERS (from Jacob's run_al.py)
############################################################

class SimpleBlockedController:
    """Serves problems in order from problem_list."""
    def __init__(self, problem_list, max_cycles=1):
        self.problem_list = problem_list
        self.index = 0
        self.max_cycles = max_cycles
        self.count = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.count >= self.max_cycles * len(self.problem_list):
            raise StopIteration

        prob = self.problem_list[self.index]
        self.index = (self.index + 1) % len(self.problem_list)
        self.count += 1
        label = prob.get("initial_problem", prob.get("fracs", ""))
        print("NEXT PROBLEM:", prob.get("domain", ""), "|", label)
        return prob


class SimpleInterleaveController:
    """Serves problems in order from problem_list (caller controls ordering)."""
    def __init__(self, problem_list, max_cycles=1):
        self.problem_list = problem_list
        self.index = 0
        self.max_cycles = max_cycles
        self.count = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.count >= self.max_cycles * len(self.problem_list):
            raise StopIteration

        prob = self.problem_list[self.index]
        self.index = (self.index + 1) % len(self.problem_list)
        self.count += 1
        label = prob.get("initial_problem", prob.get("fracs", ""))
        print("NEXT PROBLEM:", prob.get("domain", ""), "|", label)
        return prob


class BKTTrackingInterleaveController:
    """Uses BKT to track mastery and pick unmastered problems randomly."""

    def __init__(self, problem_list, bkt_probs, max_cycles=1, mastery_threshold=0.95):
        self.problem_list = problem_list
        self.index = 0
        self.max_cycles = max_cycles
        self.count = 0

        self.bkt_probs = bkt_probs
        self.mastery_threshold = mastery_threshold

        self.mastery_prob = {kc: bkt_probs[kc]["known"] for kc in bkt_probs}

        self.current_prob = None
        self.kcs_updated = set()  # tracks KCs already updated this problem (not step names)

    def __iter__(self):
        return self

    def __next__(self):
        if all(self.mastery_prob[kc] >= self.mastery_threshold for kc in self.mastery_prob):
            raise StopIteration

        if self.count >= self.max_cycles:
            raise StopIteration

        unmastered_kcs = [
            kc for kc in self.mastery_prob
            if self.mastery_prob[kc] < self.mastery_threshold
        ]

        if not unmastered_kcs:
            raise StopIteration

        candidate_probs = [
            prob for prob in self.problem_list
            if any(kc in prob.get("kc_list", []) for kc in unmastered_kcs)
        ]

        if not candidate_probs:
            raise StopIteration

        prob = choice(candidate_probs)
        prob = prob.copy() if isinstance(prob, dict) else prob

        self.count += 1
        self.current_prob = prob
        self.kcs_updated = set()

        print("UNMASTERED KCs:", unmastered_kcs)
        label = prob.get("initial_problem", prob.get("fracs", ""))
        print("NEXT PROBLEM:", label, "| KCs:", prob.get("kc_list", []))

        return prob

    def update(self, step, reward, action_type="ATTEMPT"):
        if action_type != "ATTEMPT":
            return
        if self.current_prob is None:
            return

        correct = 1 if reward > 0 else 0

        step_to_kcs = self.current_prob.get("step_to_kcs", None)
        if step_to_kcs is not None:
            kcs = step_to_kcs.get(step, [])
            # no fallback: steps not in step_to_kcs (phantom fields) produce no BKT update
        else:
            kcs = self.current_prob.get("kc_list", [])

        for kc in kcs:
            if kc in self.kcs_updated:
                # each KC is updated at most once per problem (first observation wins)
                continue
            if kc not in self.bkt_probs:
                continue

            self.kcs_updated.add(kc)

            guess = self.bkt_probs[kc]["guess"]
            slip  = self.bkt_probs[kc]["slip"]
            learn = self.bkt_probs[kc]["learn"]

            p_known = self.mastery_prob.get(kc, self.bkt_probs[kc]["known"])

            if correct == 1:
                p_obs_not_known = guess
                p_obs_known = 1 - slip
            else:
                p_obs_not_known = 1 - guess
                p_obs_known = slip

            p_not_learned = (1 - learn) * p_obs_not_known * (1 - p_known)
            p_learned = learn * p_obs_not_known * (1 - p_known) + p_obs_known * p_known

            self.mastery_prob[kc] = p_learned / (p_learned + p_not_learned)
            print(f"BKT UPDATE | step={step!r} KC={kc} correct={correct} mastery={self.mastery_prob[kc]:.4f}")


############################################################
# EXPONENT PROBLEM SETS
############################################################

bkt_probs = {
    "power_rule":    {"known": 0.2, "learn": 0.15, "guess": 0.2, "slip": 0.1},
    "product_rule":  {"known": 0.2, "learn": 0.15, "guess": 0.2, "slip": 0.1},
    "quotient_rule": {"known": 0.2, "learn": 0.15, "guess": 0.2, "slip": 0.1},
}

POWER_PROBLEMS = [
    {"domain": "exponents_power", "initial_problem": "(5^3)^4",
     "kc_list": ["power_rule"],
     "step_to_kcs": {
         "apply_power_rule": ["power_rule"],
         "simplify": ["power_rule"],
         "done": ["power_rule"],
     }},
    {"domain": "exponents_power", "initial_problem": "(2^6)^2",
     "kc_list": ["power_rule"],
     "step_to_kcs": {
         "apply_power_rule": ["power_rule"],
         "simplify": ["power_rule"],
         "done": ["power_rule"],
     }},
    {"domain": "exponents_power", "initial_problem": "(9^2)^5",
     "kc_list": ["power_rule"],
     "step_to_kcs": {
         "apply_power_rule": ["power_rule"],
         "simplify": ["power_rule"],
         "done": ["power_rule"],
     }},
    {"domain": "exponents_power", "initial_problem": "(7^4)^3",
     "kc_list": ["power_rule"],
     "step_to_kcs": {
         "apply_power_rule": ["power_rule"],
         "simplify": ["power_rule"],
         "done": ["power_rule"],
     }},
]

PRODUCT_PROBLEMS = [
    {"domain": "exponents_product", "initial_problem": "5^3 * 5^7",
     "kc_list": ["product_rule"],
     "step_to_kcs": {
         "apply_product_rule": ["product_rule"],
         "simplify": ["product_rule"],
         "done": ["product_rule"],
     }},
    {"domain": "exponents_product", "initial_problem": "3^8 * 3^2",
     "kc_list": ["product_rule"],
     "step_to_kcs": {
         "apply_product_rule": ["product_rule"],
         "simplify": ["product_rule"],
         "done": ["product_rule"],
     }},
    {"domain": "exponents_product", "initial_problem": "11^5 * 11^4",
     "kc_list": ["product_rule"],
     "step_to_kcs": {
         "apply_product_rule": ["product_rule"],
         "simplify": ["product_rule"],
         "done": ["product_rule"],
     }},
    {"domain": "exponents_product", "initial_problem": "6^9 * 6^3",
     "kc_list": ["product_rule"],
     "step_to_kcs": {
         "apply_product_rule": ["product_rule"],
         "simplify": ["product_rule"],
         "done": ["product_rule"],
     }},
]

QUOTIENT_PROBLEMS = [
    {"domain": "exponents_quotient", "initial_problem": "8^12 / 8^4",
     "kc_list": ["quotient_rule"],
     "step_to_kcs": {
         "apply_quotient_rule": ["quotient_rule"],
         "simplify": ["quotient_rule"],
         "done": ["quotient_rule"],
     }},
    {"domain": "exponents_quotient", "initial_problem": "10^9 / 10^3",
     "kc_list": ["quotient_rule"],
     "step_to_kcs": {
         "apply_quotient_rule": ["quotient_rule"],
         "simplify": ["quotient_rule"],
         "done": ["quotient_rule"],
     }},
    {"domain": "exponents_quotient", "initial_problem": "4^7 / 4^2",
     "kc_list": ["quotient_rule"],
     "step_to_kcs": {
         "apply_quotient_rule": ["quotient_rule"],
         "simplify": ["quotient_rule"],
         "done": ["quotient_rule"],
     }},
    {"domain": "exponents_quotient", "initial_problem": "12^6 / 12^1",
     "kc_list": ["quotient_rule"],
     "step_to_kcs": {
         "apply_quotient_rule": ["quotient_rule"],
         "simplify": ["quotient_rule"],
         "done": ["quotient_rule"],
     }},
]

EXPONENT_PROBLEMS = POWER_PROBLEMS + PRODUCT_PROBLEMS + QUOTIENT_PROBLEMS

# Blocked: all power, then all product, then all quotient
BLOCKED_PROBLEMS = POWER_PROBLEMS + PRODUCT_PROBLEMS + QUOTIENT_PROBLEMS

# Interleaved: power, product, quotient, power, product, quotient...
INTERLEAVED_PROBLEMS = [
    POWER_PROBLEMS[0], PRODUCT_PROBLEMS[0], QUOTIENT_PROBLEMS[0],
    POWER_PROBLEMS[1], PRODUCT_PROBLEMS[1], QUOTIENT_PROBLEMS[1],
    POWER_PROBLEMS[2], PRODUCT_PROBLEMS[2], QUOTIENT_PROBLEMS[2],
    POWER_PROBLEMS[3], PRODUCT_PROBLEMS[3], QUOTIENT_PROBLEMS[3],
]


############################################################
# FRACTION PROBLEM SETS  (Patel, Liu, Koedinger 2016 baseline)
# seed=42; denominators ≤ 12; AD uses denominator-multiplication only (no LCM)
############################################################

_bkt_default = {"known": 0.2, "learn": 0.15, "guess": 0.2, "slip": 0.1}
fraction_bkt_probs = {
    # fraction_add_same fields
    "fraction_add_same_ans_num":              dict(_bkt_default),
    "fraction_add_same_ans_den":              dict(_bkt_default),
    "fraction_add_same_done":                 dict(_bkt_default),
    # fraction_add_different fields
    "fraction_add_different_check_convert":   dict(_bkt_default),
    "fraction_add_different_conv_num1":       dict(_bkt_default),
    "fraction_add_different_conv_num2":       dict(_bkt_default),
    "fraction_add_different_conv_den1":       dict(_bkt_default),
    "fraction_add_different_conv_den2":       dict(_bkt_default),
    "fraction_add_different_ans_num":         dict(_bkt_default),
    "fraction_add_different_ans_den":         dict(_bkt_default),
    "fraction_add_different_done":            dict(_bkt_default),
    # fraction_multiply fields
    "fraction_multiply_ans_num":              dict(_bkt_default),
    "fraction_multiply_ans_den":              dict(_bkt_default),
    "fraction_multiply_done":                 dict(_bkt_default),
}

_AS_STC = {
    "ans_num": ["fraction_add_same_ans_num"],
    "ans_den": ["fraction_add_same_ans_den"],
    "done":    ["fraction_add_same_done"],
}
_AD_STC = {
    "check_convert": ["fraction_add_different_check_convert"],
    "conv_num1":     ["fraction_add_different_conv_num1"],
    "conv_num2":     ["fraction_add_different_conv_num2"],
    "conv_den1":     ["fraction_add_different_conv_den1"],
    "conv_den2":     ["fraction_add_different_conv_den2"],
    "ans_num":       ["fraction_add_different_ans_num"],
    "ans_den":       ["fraction_add_different_ans_den"],
    "done":          ["fraction_add_different_done"],
}
_M_STC = {
    "ans_num": ["fraction_multiply_ans_num"],
    "ans_den": ["fraction_multiply_ans_den"],
    "done":    ["fraction_multiply_done"],
}

def _f(op, n1, d1, n2, d2, stc):
    kc_list = list(dict.fromkeys(kc for kcs in stc.values() for kc in kcs))
    return {"op": op, "fracs": [(str(n1), str(d1)), (str(n2), str(d2))],
            "kc_list": kc_list, "step_to_kcs": stc}

FRAC_AS_PROBLEMS = [
    _f("+",  2, 12,  1, 12, _AS_STC),
    _f("+",  2,  4,  9,  4, _AS_STC),
    _f("+",  7,  3,  1,  3, _AS_STC),
    _f("+",  9,  5,  1,  5, _AS_STC),
    _f("+",  4, 10,  9, 10, _AS_STC),
    _f("+",  5, 11,  1, 11, _AS_STC),
    _f("+",  7,  4,  6,  4, _AS_STC),
    _f("+",  3,  6,  4,  6, _AS_STC),
    _f("+",  2,  8,  6,  8, _AS_STC),
    _f("+",  5,  7,  1,  7, _AS_STC),
]

FRAC_AD_PROBLEMS = [
    _f("+",  2,  9,  7, 10, _AD_STC),
    _f("+",  5,  3,  6, 10, _AD_STC),
    _f("+",  2, 11,  1,  5, _AD_STC),
    _f("+",  5, 12,  2,  5, _AD_STC),
    _f("+",  7,  5,  5,  3, _AD_STC),
    _f("+",  6,  9,  3, 12, _AD_STC),
    _f("+",  3, 10,  8,  5, _AD_STC),
    _f("+",  9,  8,  4,  6, _AD_STC),
    _f("+",  1, 12,  4,  7, _AD_STC),
    _f("+",  7,  2,  5,  7, _AD_STC),
    _f("+",  6,  3,  4,  5, _AD_STC),
    _f("+",  7, 12,  8,  9, _AD_STC),
    _f("+",  3,  4,  4,  6, _AD_STC),
    _f("+",  6, 11,  4,  8, _AD_STC),
]

FRAC_M_PROBLEMS = [
    _f("*",  8,  4,  2, 10, _M_STC),
    _f("*",  2, 12,  7,  8, _M_STC),
    _f("*",  1,  6,  2, 10, _M_STC),
    _f("*",  5, 12,  6, 10, _M_STC),
    _f("*",  7,  3,  3,  6, _M_STC),
    _f("*",  5,  9,  9,  2, _M_STC),
    _f("*",  2,  4,  5, 10, _M_STC),
    _f("*",  4, 12,  3, 10, _M_STC),
    _f("*",  9,  7,  9,  4, _M_STC),
    _f("*",  6,  2,  8, 11, _M_STC),
    _f("*",  6,  2,  5,  3, _M_STC),
    _f("*",  8,  4,  9,  4, _M_STC),
    _f("*",  9,  4,  7,  6, _M_STC),
    _f("*",  4,  5,  5, 10, _M_STC),
    _f("*",  6,  8,  8, 12, _M_STC),
    _f("*",  2, 10,  4,  9, _M_STC),
    _f("*",  6,  5,  1,  3, _M_STC),
    _f("*",  4, 11,  4, 10, _M_STC),
    _f("*",  1,  2,  4,  3, _M_STC),
    _f("*",  5, 10,  8,  5, _M_STC),
    _f("*",  3,  5,  8, 10, _M_STC),
    _f("*",  7,  5,  4,  9, _M_STC),
    _f("*",  7,  3,  6,  3, _M_STC),
    _f("*",  2, 12,  1, 12, _M_STC),
]

FRAC_ALL_PROBLEMS = FRAC_AS_PROBLEMS + FRAC_AD_PROBLEMS + FRAC_M_PROBLEMS


############################################################
# LLM AGENT CONFIGS + CLASS (unchanged from original)
############################################################

agent_configs = {
    "qwen3.5": {
        "client": "openai",
        "client_url": "https://vllm.apprentice.ai/v1",
        "model": "Qwen3.5-35B-A3B-GPTQ-Int4",
        "context_length": 3000,
        "max_prompt_length": 50000,
    },
    "qwen3.6": {
        "client": "openai",
        "client_url": "https://vllm.apprentice.ai/v1",
        "model": "models/Qwen3.6-35B-A3B-AWQ-4bit",
        "context_length": 3000,
        "max_prompt_length": 50000,
    },
    "gemma": {
        "client": "openai",
        "client_url": "https://vllm.apprentice.ai/v1",
        "model": "models/gemma-4-31B-it-AWQ-4bit",
        "context_length": 3000,
        "max_prompt_length": 50000,
    },
    "deepseek-v2.5" : {
        "client" : "ollama",
        "client_url" : 'http://localhost:11434/api/generate',
        "model" : "deepseek-v2.5",
        "context_length" : 3000,
        "max_prompt_length" : 30000,
    },
    "deepseek-r1" : {
        "client" : "ollama",
        "client_url" : 'http://localhost:11434/api/generate',
        "model": "deepseek-r1:8b",
        "context_length" : 20000,
        "max_prompt_length" : 50000,
    },
    "claude-3.5" : {
        "client" : "anthropic",
        "model" : "claude-3-5-haiku-20241022",
        "context_length" : 3000,
        "max_prompt_length" : 50000,
    },
    "gpt-4o" : {
        "client" : "openai",
        "model" : "gpt-4o",
        "context_length" : 3000,
        "max_prompt_length" : 50000,
    },
    "gpt-oss" : {
    "client" : "openai",
    "client_url" : 'https://vllm.apprentice.ai/v1',
    "model" : "models/gpt-oss-120b",
    "context_length" : 3000,
    "max_prompt_length" : 50000,
}
}

def action_semicolon_format(action):
    selection, action_type, inp = action.as_tuple()
    return f"{selection};{action_type};{inp}"

class LLMStudentAgent(LLMPromptable):
    def __init__(self, tutor_kind, config_name=None,
                 max_prompt_length=50000, **kwargs):
        config = agent_configs.get(config_name,{})
        super().__init__(tutor_kind, **config, **kwargs)
        
        self.last_state = None
        self.examples = []
        self.config_name = config_name

        self.max_prompt_length = config.get("max_prompt_length", max_prompt_length)
        
    def _manage_examples(self):
        total_chars = self.gen_prompt
        len(self.action_type_examples_prompt) + \
                      sum(len(msg["content"]) for msg in self.conversation_log)
                      
        while total_chars > self.max_prompt_length:
            print("total_chars:", total_chars)
            self.conversation_log = self.conversation_log[3:]
            total_chars = len(self.action_type_examples_prompt) + \
                          sum(len(msg["content"]) for msg in self.conversation_log)
            
    def train(self, state, action, reward, is_demo=False, is_start=False, **kwargs):

        if state != self.last_state:
            self.last_state = state
            self.examples.append([])
            self.examples[-1].append("---Start Example---")
            self.examples[-1].append(f"This is the problem state:\n{ state }\n")
            self.examples[-1].append("These are incorrect actions in this state:")

        action_str = action_semicolon_format(action)
        if is_demo or reward > 0:
            self.examples[-1].append("\nThese are correct actions in this state:")

        if self.examples[-1][-1] != f"{action_str}":
            self.examples[-1].append(f"{action_str}")

    def gen_prompt(self, state, is_start):
        full_prompt = self.action_type_examples_prompt
        full_prompt += "------Here are examples of states and incorrect and correct actions for them!------\n"
        for example in self.examples:
            full_prompt += "\n".join(example) + "\n"
        full_prompt += "------End of examples------\n"

        full_prompt += "------Now lets solve this new problem!------\n\n"
        full_prompt += self.prompts['student_act']['template'].format(
            state=state,
        )

        return full_prompt
        

    def act(self, state, is_start=False, **kwargs):
        full_prompt = self.gen_prompt(state, is_start)
        num_characters = len(full_prompt)

        while num_characters > self.max_prompt_length:
            self.examples = self.examples[1:]
            full_prompt = self.gen_prompt(state, is_start)
            num_characters = len(full_prompt)
            print("CONTEXT LIMIT REACHED - REMOVING OLDEST EXAMPLE")

        print(f"Character count: {num_characters}")

        print("PROMPT:", full_prompt)
        response = self.run_prompt_retry(full_prompt)

        print("DEBUG RAW RESPONSE:", response)
        print("TYPE:", type(response))

        if response is None:
            print("ERROR: response is None")
            return Action(("error", "error", "error"))

        if not isinstance(response, str):
            print("BAD RESPONSE TYPE:", response)
            return Action(("error", "error", "error"))

        parts = response.split(';')
        if len(parts) == 3:                
            selection, action_type, inp = parts
            if action_type == "PressButton":
                inp = -1
        elif len(parts) < 3:
            extended = parts + ['', '', '']
            extended = extended[:3]
            selection, action_type, inp = extended[0], extended[1], extended[2]
        else:
            selection, action_type, inp = 'incorrect_format', 'incorrect_format', 'incorrect_format'
        
        if(isinstance(inp, str)):
            inp = inp.replace('\\\\', '\\')    
            
        action = Action((selection, action_type, inp))        
        return action


############################################################
# RUN TRAINING FUNCTIONS
############################################################

def run_blocked(model, scaffold="all", max_cycles=1):
    """Run the blocked condition: power, power, power, product, product, product, quotient, quotient, quotient."""
    safe_model = model.replace(":", "_")
    logger = DataShopLogger("LLM_Blocked", output_dir=f'stu_eval_logs/blocked_{safe_model}')

    env = ApprenticeTutor(scaffold=scaffold)
    agent = LLMStudentAgent("apprentice", model)

    controller = SimpleBlockedController(BLOCKED_PROBLEMS, max_cycles=max_cycles)

    trainer = Trainer(agent, env, logger=logger,
                outer_loop_controller=controller,
                agent_state_repr="obj_dicts",
                num_incorrect_force_demo=2)

    trainer.start()
    print("-- BLOCKED TRAINING END --")


def run_interleaved(model, scaffold="all", max_cycles=1):
    """Run the interleaved condition: power, product, quotient, power, product, quotient..."""
    logger = DataShopLogger("LLM_Interleaved",
                extra_kcs=['field'], output_dir=f'stu_eval_logs/interleaved_{model}')

    env = ApprenticeTutor(scaffold=scaffold)
    agent = LLMStudentAgent("apprentice", model)

    controller = SimpleInterleaveController(INTERLEAVED_PROBLEMS, max_cycles=max_cycles)

    trainer = Trainer(agent, env, logger=logger,
                outer_loop_controller=controller,
                agent_state_repr="obj_dicts",
                num_incorrect_force_demo=2)

    trainer.start()
    print("-- INTERLEAVED TRAINING END --")


def run_bkt(model, scaffold="all", max_cycles=20):
    """Run the BKT condition: randomly pick unmastered problems until all KCs are mastered."""
    logger = DataShopLogger("LLM_BKT",
                extra_kcs=['field'], output_dir=f'stu_eval_logs/bkt_{model}')

    env = ApprenticeTutor(scaffold=scaffold)
    agent = LLMStudentAgent("apprentice", model)

    controller = BKTTrackingInterleaveController(
        EXPONENT_PROBLEMS,
        bkt_probs=bkt_probs,
        max_cycles=max_cycles,
        mastery_threshold=0.95
    )

    trainer = Trainer(agent, env, logger=logger,
                outer_loop_controller=controller,
                agent_state_repr="obj_dicts",
                num_incorrect_force_demo=2)

    trainer.start()
    print("-- BKT TRAINING END --")


def run_fractions_blocked(model, max_cycles=1):
    """Blocked fractions: AS block (10), then AD block (14), then M block (24).
    Order within each block is randomized each run."""
    safe_model = model.replace(":", "_")
    logger = DataShopLogger("LLM_Fractions_Blocked",
                output_dir=f'stu_eval_logs/fractions_blocked_{safe_model}')

    env = FractionArithmetic()
    agent = LLMStudentAgent("ctat", model)

    as_block = FRAC_AS_PROBLEMS.copy()
    ad_block = FRAC_AD_PROBLEMS.copy()
    m_block  = FRAC_M_PROBLEMS.copy()
    shuffle(as_block)
    shuffle(ad_block)
    shuffle(m_block)
    blocked = as_block + ad_block + m_block

    controller = SimpleBlockedController(blocked, max_cycles=max_cycles)

    trainer = Trainer(agent, env, logger=logger,
                outer_loop_controller=controller,
                agent_state_repr="obj_dicts",
                num_incorrect_force_demo=2)

    trainer.start()
    print("-- FRACTIONS BLOCKED TRAINING END --")


def run_fractions_interleaved(model, max_cycles=1):
    """Interleaved fractions: fully random ordering of all 48 problems."""
    safe_model = model.replace(":", "_")
    logger = DataShopLogger("LLM_Fractions_Interleaved",
                output_dir=f'stu_eval_logs/fractions_interleaved_{safe_model}')

    env = FractionArithmetic()
    agent = LLMStudentAgent("ctat", model)

    all_probs = FRAC_ALL_PROBLEMS.copy()
    shuffle(all_probs)

    controller = SimpleInterleaveController(all_probs, max_cycles=max_cycles)

    trainer = Trainer(agent, env, logger=logger,
                outer_loop_controller=controller,
                agent_state_repr="obj_dicts",
                num_incorrect_force_demo=2)

    trainer.start()
    print("-- FRACTIONS INTERLEAVED TRAINING END --")


def run_fractions_bkt(model, max_cycles=48):
    """BKT fractions: adaptive selection until all 3 KCs mastered or max_cycles reached."""
    safe_model = model.replace(":", "_")
    logger = DataShopLogger("LLM_Fractions_BKT",
                output_dir=f'stu_eval_logs/fractions_bkt_{safe_model}')

    env = FractionArithmetic()
    agent = LLMStudentAgent("ctat", model)

    controller = BKTTrackingInterleaveController(
        FRAC_ALL_PROBLEMS,
        bkt_probs=fraction_bkt_probs,
        max_cycles=max_cycles,
        mastery_threshold=0.95
    )

    trainer = Trainer(agent, env, logger=logger,
                outer_loop_controller=controller,
                agent_state_repr="obj_dicts",
                num_incorrect_force_demo=2)

    trainer.start()
    print("-- FRACTIONS BKT TRAINING END --")


############################################################
# MAIN
############################################################

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run LLM blocked vs interleaved experiment')
    parser.add_argument('--model', type=str, default="deepseek-v2.5",
                        choices=list(agent_configs.keys()),
                        help='The LLM model to use')
    parser.add_argument('--domain', type=str, default="exponents",
                        choices=['exponents', 'fractions'],
                        help='Which domain to run: exponents or fractions')
    parser.add_argument('--condition', type=str, default="blocked",
                        choices=['blocked', 'interleaved', 'bkt'],
                        help='Which condition to run: blocked, interleaved, or bkt')
    parser.add_argument('--max-cycles', type=int, default=1,
                        help='Number of cycles through the problem set (or max problems for bkt)')
    parser.add_argument('--scaffold', type=str, default="all",
                        help='Scaffold setting for ApprenticeTutor (exponents only)')

    args = parser.parse_args()

    print(f"Running {args.domain}/{args.condition} condition with {args.model}")

    if args.domain == "exponents":
        if args.condition == "blocked":
            run_blocked(args.model, scaffold=args.scaffold, max_cycles=args.max_cycles)
        elif args.condition == "interleaved":
            run_interleaved(args.model, scaffold=args.scaffold, max_cycles=args.max_cycles)
        elif args.condition == "bkt":
            run_bkt(args.model, scaffold=args.scaffold, max_cycles=args.max_cycles)
    elif args.domain == "fractions":
        if args.condition == "blocked":
            run_fractions_blocked(args.model, max_cycles=args.max_cycles)
        elif args.condition == "interleaved":
            run_fractions_interleaved(args.model, max_cycles=args.max_cycles)
        elif args.condition == "bkt":
            run_fractions_bkt(args.model, max_cycles=args.max_cycles)