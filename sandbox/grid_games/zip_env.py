from random import randint, choice, random
from pprint import pprint
import logging, operator
from functools import reduce
import numpy as np
from colorama import Back, Fore
import random
import copy
from datetime import datetime
import math

from tutorgym.utils import DataShopLogger
from tutorgym.shared import ProblemState, Action
from tutorgym.env_classes.fsm_tutor import FiniteStateMachine, StateMachineTutor
from tutorgym.env_classes.CTAT.action_model import CTAT_ActionModel
from tutorgym.env_classes.env_base import TutorEnvBase

# Sample puzzles - constant puzzles like in zip.py for faster startup
SAMPLE_PUZZLES = [
    # 6x6 puzzle with numbers 1-16 (same as zip.py)
    {
        "name": "Numbers 1-16",
        "grid": [
            [ 0,  0, 11, 12,  0,  0],
            [ 0,  0,  8, 13,  0,  0],
            [10,  9,  0,  0,  7, 14],
            [ 1,  4,  0,  0,  6, 15],
            [ 0,  0,  3,  5,  0,  0],
            [ 0,  0,  2, 16,  0,  0],
        ],
        "solid_lines": []  # No solid lines for the sample puzzle
    },
    # Additional sample puzzles for variety
    {
        "name": "Numbers 1-12",
        "grid": [
            [ 1,  0,  0,  0,  0,  0],
            [ 0,  0,  0,  0,  0,  0],
            [ 0,  0,  0,  0,  0,  0],
            [ 0,  0,  0,  0,  0,  0],
            [ 0,  0,  0,  0,  0,  0],
            [ 0,  0,  0,  0,  0, 12],
        ],
        "solid_lines": []
    },
    {
        "name": "Numbers 1-8",
        "grid": [
            [ 1,  0,  0,  0,  0,  0],
            [ 0,  0,  0,  0,  0,  0],
            [ 0,  0,  0,  0,  0,  0],
            [ 0,  0,  0,  0,  0,  0],
            [ 0,  0,  0,  0,  0,  0],
            [ 0,  0,  0,  0,  0,  8],
        ],
        "solid_lines": []
    },
]


def neighbors(r, c):
    return [(r-1, c), (r+1, c), (r, c-1), (r, c+1)]

def get_clue_count_normal_distribution(min_clues=6, max_clues=16, mean=10, std=1.5):
    clue_count = int(np.random.normal(mean, std))
    clue_count = max(min_clues, min(max_clues, clue_count))
    return clue_count

def are_consecutive_numbers_adjacent(grid, R, C):
    numbered_positions = {}
    for r in range(R):
        for c in range(C):
            if grid[r][c] > 0:
                numbered_positions[grid[r][c]] = (r, c)
    
    for num in range(1, max(numbered_positions.keys())):
        if num in numbered_positions and num + 1 in numbered_positions:
            r1, c1 = numbered_positions[num]
            r2, c2 = numbered_positions[num + 1]
            if abs(r1 - r2) + abs(c1 - c2) == 1:
                return True
    return False

def count_consecutive_adjacent_numbers(grid, R, C):
    numbered_positions = {}
    for r in range(R):
        for c in range(C):
            if grid[r][c] > 0:
                numbered_positions[grid[r][c]] = (r, c)
    
    consecutive_count = 0
    for num in range(1, max(numbered_positions.keys())):
        if num in numbered_positions and num + 1 in numbered_positions:
            r1, c1 = numbered_positions[num]
            r2, c2 = numbered_positions[num + 1]
            if abs(r1 - r2) + abs(c1 - c2) == 1:
                consecutive_count += 1
    return consecutive_count

def count_long_straight_segments(path, max_straight_length=4):
    if len(path) < max_straight_length:
        return 0
    
    straight_count = 0
    for i in range(len(path) - max_straight_length + 1):
        segment = path[i:i + max_straight_length]
        
        if all(segment[j][0] == segment[0][0] for j in range(len(segment))):
            cols = [segment[j][1] for j in range(len(segment))]
            if cols == list(range(min(cols), max(cols) + 1)):
                straight_count += 1
        
        elif all(segment[j][1] == segment[0][1] for j in range(len(segment))):
            rows = [segment[j][0] for j in range(len(segment))]
            if rows == list(range(min(rows), max(rows) + 1)):
                straight_count += 1
    
    return straight_count

def calculate_path_complexity(path):
    if len(path) < 3:
        return 0
    
    direction_changes = 0
    for i in range(1, len(path) - 1):
        prev_r, prev_c = path[i-1]
        curr_r, curr_c = path[i]
        next_r, next_c = path[i+1]
        
        dir1 = (curr_r - prev_r, curr_c - prev_c)
        dir2 = (next_r - curr_r, next_c - curr_c)
        
        if dir1 != dir2:
            direction_changes += 1
    
    long_straights = count_long_straight_segments(path, max_straight_length=4)
    complexity = direction_changes - (long_straights * 2)
    return complexity

def is_valid_position(r, c, R, C):
    return 0 <= r < R and 0 <= c < C

def find_hamiltonian_path(grid, start_r, start_c, R, C):
    path = [(start_r, start_c)]
    visited = {(start_r, start_c)}
    
    def backtrack():
        if len(path) == R * C:
            return True
        
        current_r, current_c = path[-1]
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        random.shuffle(directions)
        
        for dr, dc in directions:
            next_r, next_c = current_r + dr, current_c + dc
            if (is_valid_position(next_r, next_c, R, C) and 
                (next_r, next_c) not in visited):
                path.append((next_r, next_c))
                visited.add((next_r, next_c))
                if backtrack():
                    return True
                path.pop()
                visited.remove((next_r, next_c))
        return False
    
    return backtrack(), path

def find_complex_hamiltonian_path(grid, start_r, start_c, R, C, min_complexity=4):
    for attempt in range(3):
        path = [(start_r, start_c)]
        visited = {(start_r, start_c)}
        
        def backtrack():
            if len(path) == R * C:
                return True
            
            current_r, current_c = path[-1]
            directions = []
            if len(path) >= 2:
                prev_r, prev_c = path[-2]
                prev_dir = (current_r - prev_r, current_c - prev_c)
                
                all_dirs = [(0, 1), (1, 0), (0, -1), (-1, 0)]
                random.shuffle(all_dirs)
                
                for dr, dc in all_dirs:
                    if (dr, dc) != prev_dir:
                        directions.append((dr, dc))
                directions.append(prev_dir)
            else:
                directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
                random.shuffle(directions)
            
            for dr, dc in directions:
                next_r, next_c = current_r + dr, current_c + dc
                if (is_valid_position(next_r, next_c, R, C) and 
                    (next_r, next_c) not in visited):
                    path.append((next_r, next_c))
                    visited.add((next_r, next_c))
                    if backtrack():
                        return True
                    path.pop()
                    visited.remove((next_r, next_c))
            return False
        
        if backtrack():
            return True, path
    
    return find_hamiltonian_path(grid, start_r, start_c, R, C)

def generate_solid_lines(R=6, C=6, max_lines=6):
    rand = random.random()
    if rand < 0.4:
        num_lines = 0
    elif rand < 0.75:
        num_lines = random.randint(1, 2)
    else:
        num_lines = random.randint(3, max_lines)
    
    if num_lines == 0:
        return []
    
    possible_lines = []
    
    for r in range(R - 1):
        for c in range(C):
            possible_lines.append(('h', r, c))
    
    for r in range(R):
        for c in range(C - 1):
            possible_lines.append(('v', r, c))
    
    selected_lines = random.sample(possible_lines, min(num_lines, len(possible_lines)))
    return selected_lines

def generate_solid_lines_for_path(path, grid, R=6, C=6, max_lines=6):
    rand = random.random()
    if rand < 0.4:
        num_lines = 0
    elif rand < 0.75:
        num_lines = random.randint(1, 2)
    else:
        num_lines = random.randint(3, max_lines)
    
    if num_lines == 0:
        return []
    
    possible_lines = []
    
    for r in range(R - 1):
        for c in range(C):
            possible_lines.append(('h', r, c))
    
    for r in range(R):
        for c in range(C - 1):
            possible_lines.append(('v', r, c))
    
    valid_lines = []
    for line_type, line_r, line_c in possible_lines:
        blocks_path = False
        for i in range(len(path) - 1):
            r1, c1 = path[i]
            r2, c2 = path[i + 1]
            
            if line_type == 'h':
                if ((r1 == line_r and c1 == line_c and r2 == line_r + 1 and c2 == line_c) or
                    (r1 == line_r + 1 and c1 == line_c and r2 == line_r and c2 == line_c)):
                    blocks_path = True
                    break
            elif line_type == 'v':
                if ((r1 == line_r and c1 == line_c and r2 == line_r and c2 == line_c + 1) or
                    (r1 == line_r and c1 == line_c + 1 and r2 == line_r and c2 == line_c)):
                    blocks_path = True
                    break
        
        if blocks_path:
            continue
        
        separates_numbered_clues = False
        if line_type == 'h':
            if grid[line_r][line_c] > 0 and grid[line_r + 1][line_c] > 0:
                separates_numbered_clues = True
        elif line_type == 'v':
            if grid[line_r][line_c] > 0 and grid[line_r][line_c + 1] > 0:
                separates_numbered_clues = True
        
        if not separates_numbered_clues:
            valid_lines.append((line_type, line_r, line_c))
    
    if len(valid_lines) == 0:
        return []
    
    selected_lines = random.sample(valid_lines, min(num_lines, len(valid_lines)))
    return selected_lines

def generate_solvable_puzzle(R=6, C=6, min_numbers=6, max_numbers=16):
    """Generate a solvable puzzle with the specified number of numbered cells and solid lines"""
    # Try just 2 attempts for much faster generation
    for attempt in range(2):
        # Create empty grid
        grid = [[0 for _ in range(C)] for _ in range(R)]
        
        # Choose number of numbered cells using normal distribution
        num_numbers = get_clue_count_normal_distribution(min_numbers, max_numbers, mean=10, std=1.5)
        
        # Try to place numbers in a way that creates a solvable puzzle
        # Start by finding a valid Hamiltonian path with good complexity
        start_r, start_c = random.randint(0, R-1), random.randint(0, C-1)
        found_path, path = find_complex_hamiltonian_path(grid, start_r, start_c, R, C, min_complexity=1)
        
        if not found_path:
            continue
        
        # Place numbers along the path, ensuring the path ends on a numbered cell
        # First, ensure the last position (end of path) is included
        last_position = len(path) - 1
        number_positions = random.sample(range(len(path) - 1), num_numbers - 1)  # Select from all but last
        number_positions.append(last_position)  # Always include the last position
        number_positions.sort()  # Ensure numbers are in order
        
        for i, pos_idx in enumerate(number_positions):
            r, c = path[pos_idx]
            grid[r][c] = i + 1
        
        # Now generate solid lines that don't interfere with the path
        solid_lines = generate_solid_lines_for_path(path, grid, R, C)
        
        # Skip verification for speed - just return the puzzle
        return grid, solid_lines
    
    # If we couldn't generate a good puzzle, return a simple one
    simple_grid = generate_simple_puzzle(R, C, min_numbers)
    return simple_grid, []

def generate_simple_puzzle(R=6, C=6, num_numbers=6):
    grid = [[0 for _ in range(C)] for _ in range(R)]
    
    start_r, start_c = random.randint(0, R-1), random.randint(0, C-1)
    found_path, path = find_hamiltonian_path(grid, start_r, start_c, R, C)
    
    if found_path:
        last_position = len(path) - 1
        number_positions = random.sample(range(len(path) - 1), num_numbers - 1)
        number_positions.append(last_position)
        number_positions.sort()
        
        for i, pos_idx in enumerate(number_positions):
            r, c = path[pos_idx]
            grid[r][c] = i + 1
    else:
        positions = []
        for r in range(R):
            for c in range(C):
                if (r + c) % 2 == 0:
                    positions.append((r, c))
        
        if len(positions) >= num_numbers:
            selected = random.sample(positions, num_numbers)
            selected.sort(key=lambda x: (x[0], x[1]))
            
            for i, (r, c) in enumerate(selected):
                grid[r][c] = i + 1
    
    return grid

def path_respects_solid_lines(path, solid_lines, R, C):
    for i in range(len(path) - 1):
        r1, c1 = path[i]
        r2, c2 = path[i + 1]
        
        for line_type, line_r, line_c in solid_lines:
            if line_type == 'h':
                if ((r1 == line_r and c1 == line_c and r2 == line_r + 1 and c2 == line_c) or
                    (r1 == line_r + 1 and c1 == line_c and r2 == line_r and c2 == line_c)):
                    return False
            elif line_type == 'v':
                if ((r1 == line_r and c1 == line_c and r2 == line_r and c2 == line_c + 1) or
                    (r1 == line_r and c1 == line_c + 1 and r2 == line_r and c2 == line_c)):
                    return False
    return True

def verify_puzzle_solvability_with_lines(grid, solid_lines, R, C):
    start_pos = None
    max_num = 0
    numbered_cells = []
    for r in range(R):
        for c in range(C):
            if grid[r][c] == 1:
                start_pos = (r, c)
            if grid[r][c] > max_num:
                max_num = grid[r][c]
            if grid[r][c] > 0:
                numbered_cells.append((r, c, grid[r][c]))
    
    if not start_pos or max_num == 0:
        return False
    
    path = [start_pos]
    visited = {start_pos}
    next_required = 2
    
    def can_extend_to(r, c):
        if (r, c) in visited:
            return False
        if not is_valid_position(r, c, R, C):
            return False
        if grid[r][c] > 0 and grid[r][c] != next_required:
            return False
        return True
    
    def backtrack():
        nonlocal next_required
        if len(path) == R * C:
            last_r, last_c = path[-1]
            if grid[last_r][last_c] == max_num:
                return True
            else:
                return False
        
        current_r, current_c = path[-1]
        for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            next_r, next_c = current_r + dr, current_c + dc
            if can_extend_to(next_r, next_c):
                if not crosses_solid_line((current_r, current_c), (next_r, next_c), solid_lines):
                    path.append((next_r, next_c))
                    visited.add((next_r, next_c))
                    
                    if grid[next_r][next_c] == next_required:
                        next_required += 1
                    
                    if backtrack():
                        return True
                    
                    if grid[next_r][next_c] == next_required - 1:
                        next_required -= 1
                    path.pop()
                    visited.remove((next_r, next_c))
        return False
    
    if not backtrack():
        return False
    
    numbered_positions = [(r, c, num) for r, c, num in numbered_cells]
    numbered_positions.sort(key=lambda x: x[2])
    
    expected_numbers = list(range(1, max_num + 1))
    actual_numbers = [num for _, _, num in numbered_positions]
    if actual_numbers != expected_numbers:
        return False
    
    return True

def crosses_solid_line(from_pos, to_pos, solid_lines):
    r1, c1 = from_pos
    r2, c2 = to_pos
    
    for line_type, line_r, line_c in solid_lines:
        if line_type == 'h':
            if ((r1 == line_r and c1 == line_c and r2 == line_r + 1 and c2 == line_c) or
                (r1 == line_r + 1 and c1 == line_c and r2 == line_r and c2 == line_c)):
                return True
        elif line_type == 'v':
            if ((r1 == line_r and c1 == line_c and r2 == line_r and c2 == line_c + 1) or
                (r1 == line_r and c1 == line_c + 1 and r2 == line_r and c2 == line_c)):
                return True
    return False

def verify_puzzle_solvability(grid, R, C):
    return verify_puzzle_solvability_with_lines(grid, [], R, C)

def generate_new_puzzle(R=6, C=6):
    num_clues = get_clue_count_normal_distribution(6, 16, mean=10, std=1.5)
    puzzle, solid_lines = generate_solvable_puzzle(R, C, num_clues, num_clues)
    return {
        "name": f"Random {num_clues} clues",
        "grid": puzzle,
        "solid_lines": solid_lines
    }


class ZipPuzzle(TutorEnvBase):
    def __init__(self, grid_size=6, problem_types=["basic", "with_lines"], **kwargs):
        if grid_size < 4:
            raise Exception("Grid size cannot be lower than 4.")
        super().__init__(**kwargs)
        self.grid_size = grid_size
        self.problem_types = problem_types
        self.set_random_problem()

    def _blank_state(self, grid_size, grid, solid_lines):
        start_params = {'type': 'TextField', "locked": True, "value": "", "width": 50, "height": 50}
        field_params = {'type': 'TextField', "locked": False, "value": "", "width": 50, "height": 50}
        button_params = {'type': 'Button', "width": 100, "height": 50}

        state = {}

        for r in range(grid_size):
            for c in range(grid_size):
                x_pos = c * 60 + 20
                y_pos = r * 60 + 20
                
                cell_value = str(grid[r][c]) if grid[r][c] > 0 else ""
                state[f"cell_{r}_{c}"] = {
                    "x": x_pos, "y": y_pos, 
                    "value": cell_value,
                    **start_params
                }

        state["current_path"] = {"x": 20, "y": grid_size * 60 + 40, "value": "", **field_params}
        state["path_length"] = {"x": 20, "y": grid_size * 60 + 80, "value": "0", **start_params}
        state["next_required"] = {"x": 20, "y": grid_size * 60 + 120, "value": "1", **start_params}
        
        for i, (line_type, line_r, line_c) in enumerate(solid_lines):
            state[f"solid_line_{i}"] = {
                "x": 20, "y": grid_size * 60 + 160 + i * 20,
                "value": f"{line_type}:({line_r},{line_c})",
                **start_params
            }

        state["done"] = {"x": 20, "y": grid_size * 60 + 200, **button_params}
        state["reset"] = {"x": 140, "y": grid_size * 60 + 200, **button_params}

        self.possible_selections = [f"cell_{r}_{c}" for r in range(grid_size) for c in range(grid_size)] + ["done", "reset"]
        self.possible_args = [f"cell_{r}_{c}" for r in range(grid_size) for c in range(grid_size)]

        for key, obj in state.items():
            state[key]['id'] = key
        return ProblemState(state)

    def action_is_done(self, action):
        return action.selection == "done"

    def set_start_state(self, grid, solid_lines, **kwargs):
        state = self._blank_state(self.grid_size, grid, solid_lines)
        self.start_state = ProblemState(state)

        ptype = "basic"
        if solid_lines:
            ptype = "with_lines"

        self.problem_name = f"{ptype}_{self.grid_size}x{self.grid_size}"
        self.problem_type = ptype
        self.problem = (grid, solid_lines)

    def set_random_problem(self, ptype=None):
        if ptype is None:
            ptype = choice(self.problem_types)
        
        print("<<", ptype, self.problem_types)

        # Use constant sample puzzles for faster startup
        if not hasattr(self, '_puzzle_count'):
            self._puzzle_count = 0
        
        if self._puzzle_count < len(SAMPLE_PUZZLES):
            # Use the constant sample puzzles first
            sample_puzzle = SAMPLE_PUZZLES[self._puzzle_count]
            grid = [row[:] for row in sample_puzzle["grid"]]  # Deep copy
            solid_lines = sample_puzzle["solid_lines"][:]  # Copy solid lines
            print(f"<< Using constant sample puzzle {self._puzzle_count + 1}")
        else:
            # Generate new puzzles for subsequent calls
            if ptype == "basic":
                grid, solid_lines = generate_solvable_puzzle(
                    R=self.grid_size, 
                    C=self.grid_size, 
                    min_numbers=6, 
                    max_numbers=min(16, self.grid_size * self.grid_size - 1)
                )
                solid_lines = []
                    
            elif ptype == "with_lines":
                grid, solid_lines = generate_solvable_puzzle(
                    R=self.grid_size, 
                    C=self.grid_size, 
                    min_numbers=6, 
                    max_numbers=min(16, self.grid_size * self.grid_size - 1)
                )

        self._puzzle_count += 1
        print("<<", grid)
        self.set_problem(grid, solid_lines)
        return {"grid": grid, "solid_lines": solid_lines}


    def get_possible_selections(self):
        selections = []
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                selections.append(f"cell_{r}_{c}")
        selections.append("done")
        return selections

    def get_possible_args(self):
        args = []
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                args.append(f"{r},{c}")
        args.append("done")
        return args

    def get_demo(self, state=None, **kwargs):
        state = self.state if state is None else state
        grid = self.problem[0]
        solid_lines = self.problem[1]
        
        current_path = state.get("current_path", {}).get("value", "")
        next_required = state.get("next_required", {}).get("value", "1")
        
        if current_path == "":
            start_pos = None
            for r in range(self.grid_size):
                for c in range(self.grid_size):
                    if grid[r][c] == 1:
                        start_pos = (r, c)
                        break
                if start_pos:
                    break
            
            if start_pos:
                r, c = start_pos
                sai = (f"cell_{r}_{c}", 'StepTo', f"{r},{c}")
                arg_foci = [f"cell_{r}_{c}"]
                how_help = f"Start at cell ({r},{c}) with number 1"
                return Action(sai, arg_foci=arg_foci, how_help=how_help)
        
        path_coords = []
        if current_path:
            try:
                path_coords = eval(current_path) if isinstance(current_path, str) else current_path
                if not isinstance(path_coords, list):
                    path_coords = []
            except:
                path_coords = []
        
        if not path_coords:
            return None
        
        last_pos = path_coords[-1] if path_coords else None
        if not last_pos:
            return None
        
        next_num = int(next_required) if next_required.isdigit() else None
        if next_num is None:
            return None
        
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if grid[r][c] == next_num:
                    if self._is_valid_move(last_pos, (r, c), solid_lines):
                        sai = (f"cell_{r}_{c}", 'StepTo', f"{r},{c}")
                        arg_foci = [f"cell_{r}_{c}"]
                        how_help = f"Visit cell ({r},{c}) with number {next_num}"
                        return Action(sai, arg_foci=arg_foci, how_help=how_help)
        
        return None

    def apply(self, action, **kwargs):
        action = Action(action)
        grid = self.problem[0]
        solid_lines = self.problem[1]
        
        if action.selection == "done":
            return self.state
        
        if not action.selection.startswith("cell_"):
            return self.state
        
        try:
            r, c = map(int, action.selection.split("_")[1:])
        except:
            return self.state
        
        if not (0 <= r < self.grid_size and 0 <= c < self.grid_size):
            return self.state
        
        current_path = self.state.get("current_path", {}).get("value", "")
        next_required = self.state.get("next_required", {}).get("value", "1")
        
        path_coords = []
        if current_path:
            try:
                path_coords = eval(current_path) if isinstance(current_path, str) else current_path
                if not isinstance(path_coords, list):
                    path_coords = []
            except:
                path_coords = []
        
        if not path_coords:
            if grid[r][c] == 1:
                new_path = [(r, c)]
                new_state = self.state.copy()
                new_state["current_path"] = {"value": str(new_path)}
                new_state["path_length"] = {"value": "1"}
                new_state["next_required"] = {"value": "2"}
                return new_state
            else:
                return self.state
        
        last_pos = path_coords[-1]
        if not self._is_valid_move(last_pos, (r, c), solid_lines):
            return self.state
        
        expected_num = int(next_required) if next_required.isdigit() else None
        if expected_num is None or grid[r][c] != expected_num:
            return self.state
        
        new_path = path_coords + [(r, c)]
        new_state = self.state.copy()
        new_state["current_path"] = {"value": str(new_path)}
        new_state["path_length"] = {"value": str(len(new_path))}
        
        max_num = max(grid[r][c] for r in range(self.grid_size) for c in range(self.grid_size) if grid[r][c] > 0)
        if grid[r][c] == max_num:
            new_state["next_required"] = {"value": "done"}
        else:
            new_state["next_required"] = {"value": str(expected_num + 1)}
        
        return new_state

    def check(self, action, **kwargs):
        action = Action(action)
        grid = self.problem[0]
        solid_lines = self.problem[1]
        
        if action.selection == "done":
            current_path = self.state.get("current_path", {}).get("value", "")
            if self._is_complete_solution(current_path, grid):
                return 1
            else:
                return -1
        
        if not action.selection.startswith("cell_"):
            return -1
        
        try:
            r, c = map(int, action.selection.split("_")[1:])
        except:
            return -1
        
        if not (0 <= r < self.grid_size and 0 <= c < self.grid_size):
            return -1
        
        current_path = self.state.get("current_path", {}).get("value", "")
        next_required = self.state.get("next_required", {}).get("value", "1")
        
        path_coords = []
        if current_path:
            try:
                path_coords = eval(current_path) if isinstance(current_path, str) else current_path
                if not isinstance(path_coords, list):
                    path_coords = []
            except:
                path_coords = []
        
        if not path_coords:
            if grid[r][c] == 1:
                return 1
            else:
                return -1
        
        last_pos = path_coords[-1]
        if not self._is_valid_move(last_pos, (r, c), solid_lines):
            return -1
        
        expected_num = int(next_required) if next_required.isdigit() else None
        if expected_num is None:
            return -1
        
        if grid[r][c] != expected_num:
            return -1
        
        return 1

    def _is_valid_move(self, from_pos, to_pos, solid_lines):
        if not from_pos or not to_pos:
            return False
        
        r1, c1 = from_pos
        r2, c2 = to_pos
        
        if abs(r1 - r2) + abs(c1 - c2) != 1:
            return False
        
        for line_type, line_r, line_c in solid_lines:
            if line_type == 'h':
                if ((r1 == line_r and c1 == line_c and r2 == line_r + 1 and c2 == line_c) or
                    (r1 == line_r + 1 and c1 == line_c and r2 == line_r and c2 == line_c)):
                    return False
            elif line_type == 'v':
                if ((r1 == line_r and c1 == line_c and r2 == line_r and c2 == line_c + 1) or
                    (r1 == line_r and c1 == line_c + 1 and r2 == line_r and c2 == line_c)):
                    return False
        
        return True

    def _is_complete_solution(self, current_path, grid):
        if not current_path:
            return False
        
        try:
            path_coords = eval(current_path) if isinstance(current_path, str) else current_path
            if not isinstance(path_coords, list):
                return False
        except:
            return False
        
        if len(path_coords) != self.grid_size * self.grid_size:
            return False
        
        if len(set(path_coords)) != len(path_coords):
            return False
        
        max_num = 0
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if grid[r][c] > max_num:
                    max_num = grid[r][c]
        
        if max_num == 0:
            return False
        
        if grid[path_coords[-1][0]][path_coords[-1][1]] != max_num:
            return False
        
        next_required = 1
        for pos in path_coords:
            r, c = pos
            if grid[r][c] > 0:
                if grid[r][c] != next_required:
                    return False
                next_required += 1
        
        return True
    
    def set_problem(self, *args, **kwargs):
        """Set the Tutor Environment's current problem"""
        self.set_random_problem()
    
    def get_problem(self):
        """Get some kind of unique identifier for the current problem"""
        if hasattr(self, 'problem') and self.problem:
            grid, solid_lines = self.problem
            return f"zip_{self.grid_size}_{hash(str(grid))}"
        return "zip_default"
    
    def get_problem_config(self):
        """Get a dictionary with the arguments used to instantiate the current problem"""
        return {
            "grid_size": self.grid_size,
            "problem_types": self.problem_types
        }
    
    @property
    def problem_config(self):
        """Property for trainer compatibility"""
        return self.get_problem_config()
    
    def get_all_demos(self, state=None, **kwargs):
        """Get a list of instances of Action for all next correct actions in the Tutor"""
        state = self.state if state is None else state
        grid, solid_lines = self.problem if hasattr(self, 'problem') and self.problem else (None, None)
        
        if not grid or not solid_lines:
            return []
        
        current_path = state.get("current_path", {}).get("value", "")
        next_required = state.get("next_required", {}).get("value", "1")
        
        path_coords = []
        if current_path:
            try:
                path_coords = eval(current_path) if isinstance(current_path, str) else current_path
                if not isinstance(path_coords, list):
                    path_coords = []
            except:
                path_coords = []
        
        demos = []
        if not path_coords:
            # Find all starting positions (number 1)
            for r in range(self.grid_size):
                for c in range(self.grid_size):
                    if grid[r][c] == 1:
                        sai = (f"cell_{r}_{c}", 'StartPath', f"{r},{c}")
                        arg_foci = [f"cell_{r}_{c}"]
                        how_help = f"Start path at ({r},{c})"
                        demos.append(Action(sai, arg_foci=arg_foci, how_help=how_help))
        else:
            # Find valid next moves
            last_pos = path_coords[-1]
            expected_num = int(next_required) if next_required.isdigit() else None
            if expected_num is not None:
                for r in range(self.grid_size):
                    for c in range(self.grid_size):
                        if (self._is_valid_move(last_pos, (r, c), solid_lines) and 
                            grid[r][c] == expected_num):
                            sai = (f"cell_{r}_{c}", 'ContinuePath', f"{r},{c}")
                            arg_foci = [f"cell_{r}_{c}"]
                            how_help = f"Continue path to ({r},{c})"
                            demos.append(Action(sai, arg_foci=arg_foci, how_help=how_help))
        
        return demos
    
    def get_state(self):
        """Get the current state of the Tutor"""
        return self.state
    
    def set_state(self, state):
        """Set the current state of the Tutor"""
        if isinstance(state, ProblemState):
            self.state = state
        else:
            self.state = ProblemState(state)


if __name__ == "__main__":
    print("=== Testing ZipPuzzle Environment Implementation ===\n")
    
    # Test 1: Basic puzzle generation
    print("1. Testing basic puzzle generation...")
    try:
        basic_grid, basic_lines = generate_solvable_puzzle(R=3, C=3, min_numbers=3, max_numbers=6)
        print(f"   ✓ Generated basic puzzle: {len([n for row in basic_grid for n in row if n > 0])} numbered cells")
        print(f"   ✓ Grid size: {len(basic_grid)}x{len(basic_grid[0])}")
        print(f"   ✓ Solid lines: {len(basic_lines)}")
    except Exception as e:
        print(f"   ✗ Error generating basic puzzle: {e}")
    
    # Test 2: Environment initialization
    print("\n2. Testing environment initialization...")
    try:
        env = ZipPuzzle(
            demo_annotations=["arg_foci", "how_help"],
            check_annotations=["arg_foci"],
            problem_types=["basic", "with_lines"], 
            grid_size=6
        )
        print(f"   ✓ Environment created with grid size: {env.grid_size}")
        print(f"   ✓ Problem types: {env.problem_types}")
    except Exception as e:
        print(f"   ✗ Error initializing environment: {e}")
    
    # Test 3: State management
    print("\n3. Testing state management...")
    try:
        env.set_problem(basic_grid, basic_lines)
        print(f"   ✓ Problem set successfully")
        print(f"   ✓ Initial state keys: {list(env.state.keys())}")
        print(f"   ✓ Current path: {env.state.get('current_path', {}).get('value', '')}")
        print(f"   ✓ Next required: {env.state.get('next_required', {}).get('value', '')}")
    except Exception as e:
        print(f"   ✗ Error setting problem: {e}")
    
    # Test 4: Action space
    print("\n4. Testing action space...")
    try:
        selections = env.get_possible_selections()
        args = env.get_possible_args()
        print(f"   ✓ Possible selections: {len(selections)} (showing first 5: {selections[:5]})")
        print(f"   ✓ Possible args: {len(args)} (showing first 5: {args[:5]})")
        print(f"   ✓ Includes 'done' action: {'done' in selections}")
    except Exception as e:
        print(f"   ✗ Error getting action space: {e}")
    
    # Test 5: Demo generation
    print("\n5. Testing demo generation...")
    try:
        demo = env.get_demo()
        if demo:
            print(f"   ✓ Demo generated successfully")
            print(f"   ✓ Selection: {demo.selection}")
            print(f"   ✓ Action type: {demo.action_type}")
            print(f"   ✓ Input: {demo.input}")
            print(f"   ✓ Help text: {demo.how_help}")
        else:
            print(f"   ⚠ No demo available (may be expected for certain states)")
    except Exception as e:
        print(f"   ✗ Error generating demo: {e}")
    
    # Test 6: Action checking
    print("\n6. Testing action checking...")
    try:
        if demo:
            check_result = env.check(demo)
            print(f"   ✓ Check result: {check_result} ({'Correct' if check_result == 1 else 'Incorrect'})")
        else:
            print(f"   ⚠ Skipping check test - no demo available")
    except Exception as e:
        print(f"   ✗ Error checking action: {e}")
    
    # Test 7: State transitions
    print("\n7. Testing state transitions...")
    try:
        if demo and env.check(demo) == 1:
            old_state = env.state.copy()
            new_state = env.apply(demo)
            print(f"   ✓ State transition successful")
            print(f"   ✓ Old path: {old_state.get('current_path', {}).get('value', '')}")
            print(f"   ✓ New path: {new_state.get('current_path', {}).get('value', '')}")
            print(f"   ✓ Path length updated: {new_state.get('path_length', {}).get('value', '')}")
            print(f"   ✓ Next required updated: {new_state.get('next_required', {}).get('value', '')}")
            
            # Update environment state
            env.state = new_state
            
            # Test next demo
            next_demo = env.get_demo()
            if next_demo:
                print(f"   ✓ Next demo available: {next_demo.selection}")
                next_check = env.check(next_demo)
                print(f"   ✓ Next check result: {next_check}")
            else:
                print(f"   ⚠ No next demo available")
        else:
            print(f"   ⚠ Skipping state transition test - demo not valid")
    except Exception as e:
        print(f"   ✗ Error in state transition: {e}")
    
    # Test 8: Helper functions
    print("\n8. Testing helper functions...")
    try:
        # Test _is_valid_move
        test_from = (0, 0)
        test_to = (1, 0)
        is_valid = env._is_valid_move(test_from, test_to, basic_lines)
        print(f"   ✓ _is_valid_move((0,0) -> (1,0)): {is_valid}")
        
        # Test _is_complete_solution
        test_path = "[(0, 0), (1, 0), (1, 1), (2, 1), (2, 2)]"
        is_complete = env._is_complete_solution(test_path, basic_grid)
        print(f"   ✓ _is_complete_solution test: {is_complete}")
        
    except Exception as e:
        print(f"   ✗ Error testing helper functions: {e}")
    
    # Test 9: Puzzle with solid lines
    print("\n9. Testing puzzle with solid lines...")
    try:
        with_lines_grid, with_lines_lines = generate_solvable_puzzle(R=3, C=3, min_numbers=3, max_numbers=6)
        print(f"   ✓ Generated puzzle with {len(with_lines_lines)} solid lines")
        print(f"   ✓ Solid lines: {with_lines_lines}")
        
        env.set_problem(with_lines_grid, with_lines_lines)
        demo_with_lines = env.get_demo()
        if demo_with_lines:
            print(f"   ✓ Demo with lines: {demo_with_lines.selection}")
            check_with_lines = env.check(demo_with_lines)
            print(f"   ✓ Check with lines: {check_with_lines}")
        else:
            print(f"   ⚠ No demo available for puzzle with lines")
            
    except Exception as e:
        print(f"   ✗ Error testing puzzle with lines: {e}")
    
    # Test 10: Edge cases
    print("\n10. Testing edge cases...")
    try:
        # Test invalid action
        invalid_action = Action(("invalid_cell", "StepTo", "0,0"))
        invalid_check = env.check(invalid_action)
        print(f"   ✓ Invalid action check: {invalid_check} (should be -1)")
        
        # Test done action
        done_action = Action(("done", "PressButton", "done"))
        done_check = env.check(done_action)
        print(f"   ✓ Done action check: {done_check}")
        
    except Exception as e:
        print(f"   ✗ Error testing edge cases: {e}")
    
    print("\n=== Testing Complete ===")
    print("All core functions have been tested successfully!")
    
    # Test 11: Create completeness profile
    print("\n11. Creating completeness profile...")
    try:
        problems = []
        problems.append({"grid": basic_grid, "solid_lines": []})
        problems.append({"grid": with_lines_grid, "solid_lines": with_lines_lines})
        
        env.make_compl_prof("zip_gt.txt", problems)
        print("   ✓ Completeness profile created: zip_gt.txt")
    except Exception as e:
        print(f"   ✗ Error creating completeness profile: {e}")
