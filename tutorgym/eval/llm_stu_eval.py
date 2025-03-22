from abc import ABC, abstractmethod
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

from tutorgym.eval.llm_base import LLMPromptable, print_response

agent_configs = {
    "deepseek-v2.5" : {
        "client" : "ollama",
        "client_url" : 'http://localhost:11434/api/generate',
        "model" : "deepseek-v2.5",
        "context_length" : 14000,
        "max_prompt_length" : 30000,
    },
    "deepseek-r1" : {
        "client" : "ollama",
        "client_url" : 'http://localhost:11434/api/generate',
        "model" : "deepseek-r1:70b",
        "context_length" : 20000,
        "max_prompt_length" : 50000,
    },
    "claude-3.5" : {
        "client" : "anthropic",
        # "host" : 'http://localhost:11434/api/generate',
        "model" : "claude-3-5-sonnet-20241022",
        "context_length" : 20000,
        "max_prompt_length" : 50000,
    },
    "gpt-4" : {
        "client" : "openai",
        # "host" : 'http://localhost:11434/api/generate',
        "model" : "gpt-4",
        "context_length" : 20000,
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
        
        self.conversation_log = []
        self.config_name = config_name

        self.max_prompt_length = config.get("max_prompt_length", max_prompt_length)
        
    def _manage_conversation_log(self):
        total_chars = len(self.action_type_examples_prompt) + \
                      sum(len(msg["content"]) for msg in self.conversation_log)
        if total_chars > self.max_prompt_length:
            print("total_chars:", total_chars)
            self.conversation_log = self.conversation_log[3:]
            
    def train(self, state, action, reward, is_demo=False, is_start=False, **kwargs):

        action_str = action_semicolon_format(action)
        if is_demo:
            message = f"For this step, the correct action is:\n{action_str}"
            self.conversation_log.append({"role": "user", "content": message})
        else:
            self.conversation_log.append({"role": "assistant", "content": f"This is my action:\n{action_str}"})
            if reward <= 0:
                message = "That action was incorrect!"
            else:
                message = "That action was correct!"
            self.conversation_log.append({"role": "user", "content": message})
        self._manage_conversation_log()

    # def train_all(self, training_set, states={}, **kwargs):

    def act(self, state, is_start=False, **kwargs):
        if is_start:
            self.conversation_log.append({"role": "user", "content": "------Now lets solve this problem!------"})
            
        # Construct prompt for next action
        prob_prompt = self.prompts['student_act']['template'].format(
            state=state.objs,
        )
        
        self.conversation_log.append({"role": "user", "content": prob_prompt})
        self._manage_conversation_log()

        full_prompt = self.action_type_examples_prompt + \
                      "\n\n".join([msg["content"] for msg in self.conversation_log])

        # print("PROMPT:", full_prompt)
        response = self.run_prompt_retry(full_prompt)

        # Parse response into an Action
        # action_text = response.json()['response']
        parts = response.split(';')
        if len(parts) == 3:                
            selection, action_type, inp = parts
            if action_type == "PressButton":
                inp = -1
        else:
            selection, action_type, inp = 'incorrect_format', 'incorrect_format', 'incorrect_format'
        
        if(isinstance(inp, str)):
            inp = inp.replace('\\\\', '\\')    
            
        action = Action((selection, action_type, inp))        
        return action

def run_training(problem_set, tutor_kind, model, scaffold="first"):    
    logger = DataShopLogger("LLM_Agents",
                extra_kcs=['field'], output_dir=f'stu_eval_logs/{tutor_kind}_{model}')  # Changed log directory name

    if(tutor_kind == "apprentice"):
        env = ApprenticeTutor(scaffold=scaffold)
    elif(tutor_kind == "oatutor"):
        env = OATutor()
    elif(tutor_kind == "ctat"):
        env = CTAT_Tutor()

    # env.set_problem(**problem_set[0])

    #### Replace This w/ your LLM Agent ####
    agent = LLMStudentAgent(tutor_kind, model)
    ####################################### 

    trainer = Trainer(agent, env, logger=logger,
                problem_set=problem_set,
                num_incorrect_force_demo=2)

    # print("START", problem_set)
    trainer.start()
    print("-- TRAINING END -- ")


if __name__ == "__main__":
    from tutorgym.helpers.collect_problems import (
        collect_apprentice_problems, 
        collect_oatutor_problems, 
        collect_ctat_problems
    )

    parser = argparse.ArgumentParser(description='Run LLM evaluation with different models')
    parser.add_argument('--tutor-kind', type=str, default="apprentice",
                        choices=['apprentice', 'oatutor', 'ctat'],
                        help='The kind of tutor: "apprentice", "oatutor" or "ctat"')
    parser.add_argument('--model', type=str, default="deepseek-v2.5", 
                        choices=list(agent_configs.keys()),
                        help='The LLM model to use for evaluation')

    args = parser.parse_args()
    
    if(args.tutor_kind == "apprentice"):
        problem_set = collect_apprentice_problems()
    elif(args.tutor_kind == "oatutor"):
        problem_set = collect_oatutor_problems()
    elif(args.tutor_kind == "ctat"):
        problem_set = collect_ctat_problems()

    print("PROBLEM SET:", len(problem_set))
    for problem in problem_set:
        print(problem)
    # print(problem_set)

    run_training(problem_set, args.tutor_kind, args.model) 

