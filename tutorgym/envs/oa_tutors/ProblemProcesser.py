import os
import json
from typing import Dict, Optional
import random
from pathlib import Path

# Get the absolute path to ProblemPool relative to this file
current_dir = Path(__file__).parent
problem_pool_path = current_dir / "ProblemPool"  # or "../ProblemPool" if it's one level up

def read_json_file(file_path: str) -> Optional[dict]:
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading JSON file {file_path}: {e}")
        return None


def create_state_item(field: str, item_type: str, value: str, x: int, y: int, locked: bool = True) -> dict:
        return {'field': field, 'type': item_type, 'value': value, 'x': x, 'y': y, 'locked': locked}

def process_step_json(step_idx: int, step_json: dict, y: int) -> tuple[Dict, int]:
        
    state = {}
    field_prefix = f'step{step_idx}'
    
    # Add step title
    state[f'{field_prefix}_title'] = create_state_item(
        f'{field_prefix}_title', 'Label', step_json['stepTitle'], 50, y * 100
    )
    
    if step_json.get('problemType') == 'TextBox':
        # Handle TextBox type
        state[f'{field_prefix}_field'] = create_state_item(
            f'{field_prefix}_field', 'TextField', step_json['stepAnswer'][0], 50, (y + 1) * 100, False
        )
        y += 2
    else:
        # Handle RadioButton type
        for choice_idx, choice in enumerate(step_json['choices']):
            state[f'{field_prefix}_choice{choice_idx}'] = {
                **create_state_item(f'{field_prefix}_choice{choice_idx}', 'RadioButton', choice, 50, (y + 1) * 100, False),
                'selected': False
            }
            y += 2
    
    return state, y

def process_problem_pool(problem_name: str) -> tuple[dict, dict]:

    # Get list of matching problem directories and randomly select one
    matching_dirs = [d for d in os.listdir(problem_pool_path) 
                    if problem_name in d and os.path.isdir(os.path.join(problem_pool_path, d))]
    if not matching_dirs:
        print(f"No directories found containing '{problem_name}'")
        return
        
    problem_dir = random.choice(matching_dirs)
    state: dict[str, dict] = {}
    answers: dict[str, str] = {}

    y = 0
    problem_dir_path = os.path.join(problem_pool_path, problem_dir)
    
    # Process problem JSON files
    for json_file in [f for f in os.listdir(problem_dir_path) if f.endswith('.json')]:
        json_path = os.path.join(problem_dir_path, json_file)
        
        if problem_json := read_json_file(json_path):
            if all(key in problem_json for key in ['body', 'title']):
                state['title'] = create_state_item('problem_name', 'Label', problem_json['title'], 50, y * 100)
                state['body'] = create_state_item('problem_description', 'Label', problem_json['body'], 50, (y + 1) * 100)
                y += 2

    # Process steps
    steps_dir = os.path.join(problem_dir_path, "steps")
    if os.path.exists(steps_dir):
        for step_idx, step_dir in enumerate(sorted(os.listdir(steps_dir))):
            step_dir_path = os.path.join(steps_dir, step_dir)
            
            if not os.path.isdir(step_dir_path):
                continue
            
            for json_file in [f for f in os.listdir(step_dir_path) if f.endswith('.json')]:
                if step_json := read_json_file(os.path.join(step_dir_path, json_file)):
                    step_state, y = process_step_json(step_idx, step_json, y)
                    state.update(step_state)
                    answers[f'step{step_idx}'] = step_json['stepAnswer'][0]
    return state, answers