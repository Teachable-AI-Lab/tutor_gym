from abc import ABC, abstractmethod
from tutorgym.utils import unique_hash
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

action_types_by_tutor_kind = {
    "apprentice" : ["input change", "PressButton"],
    "oatutor" : ["UpdateTextField", "PressButton"] ,
    "ctat" : ["UpdateTextField", "UpdateRadioButton", "PressButton"] ,
}

class LLMEvaluator(ABC):
    def __init__(self, model_name, tutor_kind):
        self.model_name = model_name
        self.tutor_kind = tutor_kind
        self.action_types = action_types_by_tutor_kind[tutor_kind]

        
        # Load prompts from YAML
        prompts_path = Path(__file__).parent / "prompts.yaml"
        with open(prompts_path, 'r') as f:
            self.prompts = yaml.safe_load(f)
        
    @abstractmethod
    def run_prompt(self, prompt, max_tokens=100):
        """Get response from LLM model"""
        pass

    def initialize_csv_files(self, profile_path):
        """Initialize CSV files with headers"""
        prof_name = pathlib.Path(profile_path).parts[-1].split(".")[0]

        now_str = ""
        now = datetime.now()
        now_str = now.strftime('%Y-%m-%d-%H-%M-%S')

        tutor_kind, model = self.tutor_kind, self.model_name

        directory = f"tutor_eval_logs/{prof_name}_{model}/{now_str}"
        os.makedirs(directory, exist_ok=True)
        
        self.action_csv = f'{directory}/action_check.csv'
        self.corr_csv = f'{directory}/correct_check.csv'
        self.incorr_csv = f'{directory}/incorrect_check.csv'

        with open(f"{directory}/PROFILE_HASH", 'w') as f:
            f.write(self.profile_hash)

        with open(self.action_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['hash_id', 'domain', 'selection', 'action_type', 'input', 'action_is_correct'])
        
        with open(self.corr_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['hash_id', 'domain', 'selection', 'action_type', 'input', 'action_is_correct', 'response', 'response_is_correct'])
        
        with open(self.incorr_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['hash_id', 'domain', 'selection', 'action_type', 'input', 'action_is_correct', 'response', 'response_is_correct'])

    def get_next_action(self, state, domain):
        domain_name = ' '.join(domain.replace('htn_', '').split('_'))
        next_action_message = self.prompts['next_action']['template'].format(
            domain_name=domain_name,
            state=state,
            action_types=self.action_types
        )
        return self.run_prompt(next_action_message)

    def verify_actions(self, state, domain, actions, action_is_correct=True):
        # true_correctness = "Correct" if is_correct else "Incorrect"
        domain_name = ' '.join(domain.replace('htn_', '').split('_'))

        results = []
        for act_d in actions:

            action_str = f"{act_d['selection']};{act_d['action_type']};{act_d['inputs']['value']}"

            verify_message = self.prompts['verify_action']['template'].format(
                domain_name=domain_name,
                state=state,
                action_types=self.action_types,
                action=action_str
            )

            # Print w/ encode to avoid possible unicode errors  
            print(verify_message.encode(sys.stdout.encoding, 'replace'))

            response = self.run_prompt(verify_message)
            results.append((
                act_d['selection'],
                act_d['action_type'],
                act_d['inputs']['value'], 
                action_is_correct,
                response.lower(),
                response.lower() == 'yes',
            ))

            # responses.append((true_correctness, act_d, response))
            print(action_is_correct, response)
        return results
    
    def evaluate(self, profile_path="apprentince_compl.prof"):

        with open(profile_path, 'r') as profile:
            lines = [line for line in profile]
            total_lines = len(lines)
            self.profile_hash = unique_hash(lines)

        self.initialize_csv_files(profile_path)
                
        with open(profile_path, 'r') as profile:
            progress_bar = tqdm(total=total_lines, desc=f"Processing examples with {self.model_name}")
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
            obj['domain'] = obj['problem']

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
                action['inputs']['value'] == inp_val
                for action in obj['correct_actions']
            )

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

        # for result in incorr_results:
        #     sai, correctness, action, response = result

        #     filename = self.corr_csv if correctness == "Correct" else self.incorr_csv #f'{self.tutor_name}_{"correctness" if correctness == "Correct" else "incorrectness"}_check_{self.model_name}.csv'
            
                
        #         writer.writerow([hash_id, domain, 
        #                         (selection, action_type, input)
        #                         response.lower() == ('yes' if correctness == "Correct" else 'no')])

def get_evaluator_class(model: str) -> Type[LLMEvaluator]:
    """Get the appropriate evaluator class based on model name"""
    from tutorgym.eval.llm_eval_anthropic import AnthropicEvaluator
    from tutorgym.eval.llm_eval_openai import OpenAIEvaluator
    from tutorgym.eval.llm_eval_deepseek import DeepseekEvaluator

    evaluators: Dict[str, Type[LLMEvaluator]] = {
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
    parser.add_argument('--model', type=str, required=True, 
                       choices=['anthropic', 'openai', 'deepseek'],
                       help='The LLM model to use for evaluation')
    parser.add_argument('--profile', type=str, default="apprentice_compl.prof",
                       help='Path to the profile file (default: apprentice_compl.prof)')
    parser.add_argument('--tutor-kind', type=str, default=None,
                       help='The tutor tutor_kind: "apprentice", "oatutor" or "ctat"')
    
    args = parser.parse_args()
    tutor_kind = args.tutor_kind
    tutor_kind = tutor_kind if tutor_kind else guess_tutor_kind(args.profile)
    if(tutor_kind is None):
        raise ValueError('Could not deduce tutor kind from from profile name ' +
         'please provide --tutor-kind="apprentice", "oatutor" or "ctat"')
    
    # Get and instantiate the appropriate evaluator
    evaluator_class = get_evaluator_class(args.model)
    evaluator = evaluator_class(tutor_kind)
    
    # Run evaluation
    evaluator.evaluate(args.profile)

if __name__ == "__main__":
    main() 
