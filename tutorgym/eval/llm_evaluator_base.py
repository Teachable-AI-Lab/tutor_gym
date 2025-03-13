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
import datetime
import os

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
    def get_completion(self, prompt, max_tokens=100):
        """Get completion from LLM model"""
        pass

    def initialize_csv_files(self, log_start_time=False):
        """Initialize CSV files with headers"""
        # tutor_kind, model = self.tutor_kind, self.model_name

        now_str = ""
        if(log_start_time):
            now = datetime.now().timestamp()
            now_str = "_" + now.strftime('%Y-%m-%d-%H-%M-%S')

        tutor_kind, model = self.tutor_kind, self.model_name
        self.action_csv = f'tutor_eval_logs/{tutor_kind}_action_check_{model}{now_str}.csv'
        self.corr_csv = f'tutor_eval_logs/{tutor_kind}_correct_check_{model}{now_str}.csv'
        self.incorr_csv = f'tutor_eval_logs/{tutor_kind}_incorrect_check_{model}{now_str}.csv'

        os.makedirs("tutor_eval_logs", exist_ok=True)

        with open(self.action_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['hash_id', 'domain', 'action', 'action_correct'])
        
        with open(self.corr_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['hash_id', 'domain', 'correct'])
        
        with open(self.incorr_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['hash_id', 'domain', 'incorrect'])

    def get_next_action(self, state, domain):
        domain_name = ' '.join(domain.replace('htn_', '').split('_'))
        next_action_message = self.prompts['next_action']['template'].format(
            domain_name=domain_name,
            state=state,
            action_types=self.action_types
        )
        return self.get_completion(next_action_message)

    def verify_actions(self, state, domain, actions, is_correct=True):
        true_correctness = "Correct" if is_correct else "Incorrect"
        domain_name = ' '.join(domain.replace('htn_', '').split('_'))

        responses = []
        for act_d in actions:

            action_str = f"{act_d['selection']};{act_d['action_type']};{act_d['inputs']['value']}"

            verify_message = self.prompts['verify_action']['template'].format(
                domain_name=domain_name,
                state=state,
                action_types=self.action_types,
                action=action_str
            )
            print(verify_message)
            response = self.get_completion(verify_message)
            responses.append((true_correctness, act_d, response))
            print(true_correctness, response)
        return responses
    
    def evaluate(self, profile_path="apprentince_compl.prof", log_start_time=False):
        self.initialize_csv_files(log_start_time)
        
        with open(profile_path, 'r') as profile:
            total_lines = sum(1 for _ in profile)
        
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
                selection, action_type, input = 'incorrect_format', 'incorrect_format', 'incorrect_format'
            else:
                selection, action_type, input = parts
        except Exception:
            selection, action_type, input = 'incorrect_format', 'incorrect_format', 'incorrect_format'

        next_action_correct = False
        if selection != 'incorrect_format':
            next_action_correct = any(
                action['selection'] == selection and 
                action['action_type'] == action_type and 
                action['inputs']['value'] == input
                for action in obj['correct_actions']
            )

        correct_verified = self.verify_actions(filtered_state, obj['domain'], obj['correct_actions'], True)
        incorrect_verified = self.verify_actions(filtered_state, obj['domain'], obj['incorrect_actions'], False)

        try:
            self._write_results(hash_id, obj['domain'], selection, action_type, input, next_action_correct, correct_verified, incorrect_verified)
        except Exception as e:
            print(f"Error writing to CSV: {str(e)}")
        
        progress_bar.update(1)

    def _write_results(self, hash_id, domain, selection, action_type, input, next_action_correct, correct_verified, incorrect_verified):
        with open(self.action_csv, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([hash_id, domain, (selection, action_type, input), next_action_correct])
        
        for result in [*correct_verified, *incorrect_verified]:
            correctness, action, response = result

            filename = self.corr_csv if correctness == "Correct" else self.incorr_csv #f'{self.tutor_name}_{"correctness" if correctness == "Correct" else "incorrectness"}_check_{self.model_name}.csv'
            with open(filename, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([hash_id, domain, response.lower() == ('yes' if correctness == "Correct" else 'no')])

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
    parser.add_argument('--tutor_kind', type=str, default=None,
                       help='The tutor tutor_kind: "apprentice", "oatutor" or "ctat"')
    
    args = parser.parse_args()
    tutor_kind = args.tutor_kind
    tutor_kind = tutor_kind if tutor_kind else guess_tutor_kind(args.profile)
    
    # Get and instantiate the appropriate evaluator
    evaluator_class = get_evaluator_class(args.model)
    evaluator = evaluator_class(tutor_kind)
    
    # Run evaluation
    evaluator.evaluate(args.profile)

if __name__ == "__main__":
    main() 
