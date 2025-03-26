from abc import ABC, abstractmethod
from tutorgym.utils import unique_hash, as_sympy_str
from tutorgym.shared import Action
import json
import csv
from tqdm import tqdm
import yaml
from pathlib import Path
import argparse
from typing import Type, Dict
from datetime import datetime
import os
import sys
import pathlib
from tutorgym.eval.llm_base import LLMPromptable, print_response, action_types_by_tutor_kind, print_green, print_red
from colorama import Back, Fore, Style

agent_configs = {
    "deepseek-v2.5" : {
        "client" : "ollama",
        "client_url" : 'http://localhost:11434/api/generate',
        "model" : "deepseek-v2.5",
        "context_length" : 6000,
    },
    "deepseek-r1" : {
        "client" : "ollama",
        "client_url" : 'http://localhost:11434/api/generate',
        "model" : "deepseek-r1:70b",
        "context_length" : 6000,
    }
}

class LLMTutorEvaluator(LLMPromptable):
    def __init__(self, tutor_kind, config_name=None, **kwargs):
        config = agent_configs.get(config_name,{})
        super().__init__(tutor_kind, **config, **kwargs)

        # Load special domain prompts
        path = f'{tutor_kind}_prompts.yaml'
        if(os.path.exists(path)):
            with open(path, 'r') as f:
                self.domain_prompts = yaml.safe_load(f)
        else:
            self.domain_prompts = {}


    def initialize_csv_files(self, profile_path, total_lines):
        """Initialize CSV files with headers"""
        prof_name = pathlib.Path(profile_path).parts[-1].split(".")[0]

        now_str = ""
        now = datetime.now()
        now_str = now.strftime('%Y-%m-%d-%H-%M-%S')

        tutor_kind, model = self.tutor_kind, self.model

        directory = f"tutor_eval_logs/{prof_name}_{model}/{now_str}"
        os.makedirs(directory, exist_ok=True)
        
        self.action_csv = f'{directory}/action_check.csv'
        self.corr_csv = f'{directory}/correct_check.csv'
        self.incorr_csv = f'{directory}/incorrect_check.csv'

        with open(f"{directory}/profile_info.json", 'w') as f:
            json.dump({
                "profile_hash" : self.profile_hash,
                "profile_name" : prof_name,
                "profile_num_lines" : total_lines
                }
            , f)

        with open(self.action_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['hash_id', 'domain', 'selection', 'action_type', 'input', 'action_is_correct'])
        
        with open(self.corr_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['hash_id', 'domain', 'selection', 'action_type', 'input', 'action_is_correct', 'response', 'response_is_correct'])
        
        with open(self.incorr_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['hash_id', 'domain', 'selection', 'action_type', 'input', 'action_is_correct', 'response', 'response_is_correct'])

    def _resolve_domain_name(self, domain):
        if(isinstance(domain, list)):
            domain = domain[-1]

        domain_name = ' '.join(domain.replace('htn_', '').split('_'))

        print("DOMAIN:", domain, domain_name)
        return domain, domain_name

    def get_next_action(self, state, domain):
        domain, domain_name = self._resolve_domain_name(domain)

        next_action_message = self.action_type_examples_prompt + \
            self.prompts['next_action']['template'].format(
                tutor_behavior_description=self.domain_prompts.get(domain, ""),
                domain_name=domain_name,
                state=state,
                action_types=self.action_types
        )

        # Print w/ encode to avoid possible unicode errors  
        # print(next_action_message.encode(sys.stdout.encoding, 'replace').decode("utf-8"))

        return self.run_prompt_retry(next_action_message)

    def verify_actions(self, state, domain, actions, action_is_correct=True):
        domain, domain_name = self._resolve_domain_name(domain)

        results = []
        for act_d in actions:

            action_str = f"{act_d['selection']};{act_d['action_type']};{act_d['input']}"

            verify_message = self.action_type_examples_prompt + \
                self.prompts['verify_action']['template'].format(
                    tutor_behavior_description=self.domain_prompts.get(domain, ""),
                    domain_name=domain_name,
                    state=state,
                    action_types=self.action_types,
                    action=action_str
            )

            # Print w/ encode to avoid possible unicode errors  
            # print(verify_message.encode(sys.stdout.encoding, 'replace').decode("utf-8"))

            response = self.run_prompt_retry(verify_message)
            ideal_response = 'yes' if action_is_correct else "no"
            results.append((
                act_d['selection'],
                act_d['action_type'],
                act_d['input'], 
                action_is_correct,
                response.lower(),
                response.lower() == ideal_response,
            ))

            if(response.lower() == ideal_response):
                print_green(response)
            else:
                print_red(response)

            # responses.append((true_correctness, act_d, response))
            # print("RESPONSE:", action_is_correct, response)
        return results
    
    def evaluate(self, profile_path="apprentince_compl.prof"):

        with open(profile_path, 'r') as profile:
            lines = [line for line in profile]
            total_lines = len(lines)
            self.profile_hash = unique_hash(lines)

        self.initialize_csv_files(profile_path, total_lines)
                
        with open(profile_path, 'r') as profile:
            progress_bar = tqdm(total=total_lines, desc=f"Processing examples with {self.model}")
            while line := profile.readline():
                self._process_line(line, progress_bar)
            progress_bar.close()

    def _process_line(self, line, progress_bar):
        obj = json.loads(line)
        hash_id = unique_hash(line)
        
        if self.tutor_kind == "apprentice":
            current_scaffold_level = int(obj['scaffold'].split('_')[-1])
            filtered_state = {
                k: v for k, v in obj['state'].items()
                if 'scaffold_level' not in v or 
                int(v['scaffold_level'].split('_')[-1]) <= current_scaffold_level
            }
        else:
            filtered_state = obj['state']

        next_action_response = self.get_next_action(filtered_state, obj['domain'])
        
        try:
            parts = next_action_response.split(';')
            if len(parts) != 3:
                selection, action_type, inp_val = 'incorrect_format', 'incorrect_format', 'incorrect_format'
            else:
                selection, action_type, inp_val = parts
        except Exception:
            selection, action_type, inp_val = 'incorrect_format', 'incorrect_format', 'incorrect_format'

        next_action_correct = False
        if selection != 'incorrect_format':
            next_action_correct = any(
                action['selection'] == selection and 
                action['action_type'] == action_type and 
                (str(action['input']) == str(inp_val) or as_sympy_str(action['input']) == as_sympy_str(inp_val))
                for action in obj['correct_actions']
            )

        if(next_action_correct):
            print_green(next_action_response.encode(sys.stdout.encoding, 'replace').decode('utf-8'))
        else:
            print_red(next_action_response.encode(sys.stdout.encoding, 'replace').decode('utf-8'))

        corr_results = self.verify_actions(filtered_state, obj['domain'], obj['correct_actions'], True)
        incorr_results = self.verify_actions(filtered_state, obj['domain'], obj['incorrect_actions'], False)

        try:
            self._write_results(obj, hash_id, obj['domain'], selection, action_type, inp_val, next_action_correct, corr_results, incorr_results)
        except Exception as e:
            print(f"Error writing to CSV: {str(e)}")
        
        progress_bar.update(1)

    def _write_results(self, obj, hash_id, domain, selection, action_type, inp_val, next_action_correct, corr_results, incorr_results):
        with open(self.action_csv, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([hash_id, domain, selection, action_type, inp_val, next_action_correct])
        
        with open(self.corr_csv, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            for result_row in corr_results:
                writer.writerow([hash_id, domain, *result_row])

        with open(self.incorr_csv, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            for result_row in incorr_results:
                writer.writerow([hash_id, domain, *result_row])


def get_evaluator_class(model: str) -> Type[LLMTutorEvaluator]:
    """Get the appropriate evaluator class based on model name"""
    from tutorgym.eval.llm_eval_anthropic import AnthropicEvaluator
    from tutorgym.eval.llm_eval_openai import OpenAIEvaluator
    from tutorgym.eval.llm_eval_deepseek import DeepseekEvaluator

    evaluators: Dict[str, Type[LLMTutorEvaluator]] = {
        'anthropic': AnthropicEvaluator,
        'openai': OpenAIEvaluator,
        'deepseek': DeepseekEvaluator
    }
    
    if model not in evaluators:
        raise ValueError(f"Unknown model: {model}. Available models: {list(evaluators.keys())}")
    
    return evaluators[model]

def guess_tutor_kind(profile_name):
    for tutor_kind in action_types_by_tutor_kind:
        if(tutor_kind in profile_name):
            return tutor_kind
    return None


def main():
    parser = argparse.ArgumentParser(description='Run LLM evaluation with different models')
    parser.add_argument('--tutor-kind', type=str, default=None,
                       help='The tutor tutor_kind: "apprentice", "oatutor" or "ctat"')
    parser.add_argument('--model', type=str, default="deepseek-v2.5", 
                       choices=list(agent_configs.keys()),
                       help='The LLM model to use for evaluation')
    parser.add_argument('--profile', type=str, default="apprentice_compl.prof",
                       help='Path to the profile file (default: apprentice_compl.prof)')
    
    args = parser.parse_args()

    # Try to deduce tutor_kind from profile name
    tutor_kind = args.tutor_kind
    if(tutor_kind is None):
        tutor_kind = guess_tutor_kind(args.profile)
    if(tutor_kind is None):
        raise ValueError('Could not deduce tutor kind from from profile name ' +
         'please provide --tutor-kind="apprentice", "oatutor" or "ctat"')
    
    # Get and instantiate the appropriate evaluator
    evaluator = LLMTutorEvaluator(tutor_kind, args.model)
    
    # Run evaluation
    evaluator.evaluate(args.profile)

if __name__ == "__main__":
    main() 
