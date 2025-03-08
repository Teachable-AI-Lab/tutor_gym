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

class LLMEvaluator(ABC):
    def __init__(self, model_name):
        self.model_name = model_name
        self.tutor_name = "apprentice"
        
        # Load prompts from YAML
        prompts_path = Path(__file__).parent / "prompts.yaml"
        with open(prompts_path, 'r') as f:
            self.prompts = yaml.safe_load(f)
        
    @abstractmethod
    def get_completion(self, prompt, max_tokens=100):
        """Get completion from LLM model"""
        pass

    def initialize_csv_files(self, tutor_name):
        """Initialize CSV files with headers"""
        with open(f'{tutor_name}_action_check_{self.model_name}.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['hash_id', 'domain', 'action', 'action_correct'])
        
        with open(f'{tutor_name}_correctness_check_{self.model_name}.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['hash_id', 'domain', 'correct'])
        
        with open(f'{tutor_name}_incorrectness_check_{self.model_name}.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['hash_id', 'domain', 'incorrect'])

    def get_next_action(self, state, domain):
        domain_name = ' '.join(domain.replace('htn_', '').split('_'))
        next_action_message = self.prompts['next_action']['template'].format(
            domain_name=domain_name,
            state=state
        )
        return self.get_completion(next_action_message)

    def verify_actions(self, state, domain, actions, is_correct=True):
        action_type = "Correct" if is_correct else "Incorrect"
        domain_name = ' '.join(domain.replace('htn_', '').split('_'))

        responses = []
        for action in actions:
            verify_message = self.prompts['verify_action']['template'].format(
                domain_name=domain_name,
                state=state,
                action=Action(action).sai
            )
            response = self.get_completion(verify_message)
            responses.append((action_type, action, response))
        return responses
    
    def evaluate(self, profile_path="apprentince_compl.prof"):
        self.tutor_name = profile_path.split('_')[0]
        self.initialize_csv_files(self.tutor_name)
        
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
        
        if self.tutor_name == "apprentice":
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

        correct_verified = self.verify_actions(filtered_state, obj['domain'], obj['correct_actions'], True)
        incorrect_verified = self.verify_actions(filtered_state, obj['domain'], obj['incorrect_actions'], False)

        is_correct = False
        if selection != 'incorrect_format':
            is_correct = any(
                action['selection'] == selection and 
                action['action_type'] == action_type and 
                action['inputs']['value'] == input
                for action in obj['correct_actions']
            )
        
        try:
            self._write_results(hash_id, obj['domain'], selection, action_type, input, is_correct, correct_verified, incorrect_verified)
        except Exception as e:
            print(f"Error writing to CSV: {str(e)}")
        
        progress_bar.update(1)

    def _write_results(self, hash_id, domain, selection, action_type, input, is_correct, correct_verified, incorrect_verified):
        with open(f'{self.tutor_name}_action_check_{self.model_name}.csv', 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([hash_id, domain, (selection, action_type, input), is_correct])
        
        for result in [*correct_verified, *incorrect_verified]:
            action_type, action, response = result
            filename = f'{self.tutor_name}_{"correctness" if action_type == "Correct" else "incorrectness"}_check_{self.model_name}.csv'
            with open(filename, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([hash_id, domain, response.lower() == ('yes' if action_type == "Correct" else 'no')])

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

def main():
    parser = argparse.ArgumentParser(description='Run LLM evaluation with different models')
    parser.add_argument('--model', type=str, required=True, 
                       choices=['anthropic', 'openai', 'deepseek'],
                       help='The LLM model to use for evaluation')
    parser.add_argument('--profile', type=str, default="apprentice_compl.prof",
                       help='Path to the profile file (default: apprentice_compl.prof)')
    
    args = parser.parse_args()
    
    # Get and instantiate the appropriate evaluator
    evaluator_class = get_evaluator_class(args.model)
    evaluator = evaluator_class()
    
    # Run evaluation
    evaluator.evaluate(args.profile)

if __name__ == "__main__":
    main() 