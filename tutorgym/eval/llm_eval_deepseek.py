from tutorgym.utils import unique_hash
from tutorgym.shared import Action
import json
import csv
from tqdm import tqdm
import time
import requests  # Add this import at the top

# Remove the Anthropic import and client initialization
# from anthropic import Anthropic
# anthropic = Anthropic()

# Initialize CSV files with headers
def initialize_csv_files():
    with open('action_check_anthropic.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['hash_id', 'domain', 'action', 'action_correct'])
    
    with open('correctness_check_anthropic.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['hash_id', 'domain', 'correct'])
    
    with open('incorrectness_check_anthropic.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['hash_id', 'domain', 'incorrect'])

def get_next_action(state, domain):
    next_action_message = f"""
I need your help solving this {' '.join(domain.replace('htn_', '').split('_'))} problem. This is the problem state:
{state}

I need you to give me the next action for this problem state. You are only only allowed to changed a field with 'locked' \
as False. I need your response in this format: field;action_type;value, where:
1. field is name of the field. 
2. action_type can either be either "input change" or "PressButton"
3. value is the value to enter that field. 
Avoid additional text.
    """

    response = requests.post('http://localhost:11434/api/generate', json={
        'model': 'deepseek-v2.5',
        'prompt': next_action_message,
        'stream': False
    })
    return response.json()['response']

def verify_actions(state, domain, actions, is_correct=True):
    action_type = "Correct" if is_correct else "Incorrect"
    actions_str = "\n".join([f"- {Action(action)}" for action in actions])
    verify_message = f"""
Given this problem state for {' '.join(domain.replace('htn_', '').split('_'))}:
{state}

Are any of these actions correct?
{actions_str}

Answer only with 'yes' or 'no'.
    """
    time.sleep(1)  # Add delay before API call
    response = requests.post('http://localhost:11434/api/generate', json={
        'model': 'deepseek-v2.5',
        'prompt': verify_message,
        'stream': False
    })
    return action_type, actions, response.json()['response']

def main():
    initialize_csv_files()
    
    # Count total lines first
    with open("apprentince_compl.prof", 'r') as profile:
        total_lines = sum(1 for _ in profile)
    
    # Reopen file for processing
    with open("apprentince_compl.prof", 'r') as profile:
        progress_bar = tqdm(total=total_lines, desc="Processing examples")
        while line := profile.readline():
            obj = json.loads(line)
            hash_id = unique_hash(line)
            
            current_scaffold_level = int(obj['scaffold'].split('_')[-1])
            filtered_state = {
                k: v for k, v in obj['state'].items()
                if 'scaffold_level' not in v or 
                int(v['scaffold_level'].split('_')[-1]) <= current_scaffold_level
            }

            # Sequential API calls instead of concurrent
            next_action_response = get_next_action(filtered_state, obj['domain'])
            next_action_response = get_next_action(filtered_state, obj['domain'])
            
            # Check if response format is correct
            try:
                parts = next_action_response.split(';')
                if len(parts) != 3:
                    selection, action_type, input = 'incorrect_format', 'incorrect_format', 'incorrect_format'
                else:
                    selection, action_type, input = parts
            except Exception as e:
                selection, action_type, input = 'incorrect_format', 'incorrect_format', 'incorrect_format'

            correct_verify = verify_actions(filtered_state, obj['domain'], obj['correct_actions'], True)
            incorrect_verify = verify_actions(filtered_state, obj['domain'], obj['incorrect_actions'], False)

            # Process results sequentially
            is_correct = False
            if selection != 'incorrect_format':
                is_correct = any(action['selection'] == selection and action['action_type'] == action_type and action['inputs']['value'] == input
                               for action in obj['correct_actions'])
            
            try:
                with open('action_check_anthropic.csv', 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([hash_id, obj['domain'], (selection, action_type, input), is_correct])
                
                # Process verification results
                for result in [correct_verify, incorrect_verify]:
                    action_type, actions, response = result
                    if action_type == "Correct":
                        with open('correctness_check_anthropic.csv', 'a', newline='', encoding='utf-8') as f:
                            writer = csv.writer(f)
                            writer.writerow([hash_id, obj['domain'], response.lower() == 'yes'])
                    else:
                        with open('incorrectness_check_anthropic.csv', 'a', newline='', encoding='utf-8') as f:
                            writer = csv.writer(f)
                            writer.writerow([hash_id, obj['domain'], response.lower() == 'no'])
            except Exception as e:
                print(f"Error writing to CSV: {str(e)}")
                continue
            
            progress_bar.update(1)
        progress_bar.close()

# Update main execution
if __name__ == "__main__":
    main()