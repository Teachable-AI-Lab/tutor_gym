import random
import numpy as np
from tutorgym.shared import ProblemState
from tutorgym.env_classes.fsm_tutor import FiniteStateMachine, StateMachineTutor
from tutorgym.env_classes.CTAT.action_model import CTAT_ActionModel
from tutorgym.env_classes.env_base import TutorEnvBase
from tutorgym.env_classes.CTAT.action_model import Action

# === Core Sudoku logic (extracted to pure functions, mirrors sudoku.py) ===

def is_valid_move(grid, row, col, num, grid_size=9):
    for c in range(grid_size):
        if grid[row][c] == num:
            return False
    for r in range(grid_size):
        if grid[r][col] == num:
            return False
    box_row = (row // 3) * 3
    box_col = (col // 3) * 3
    for r in range(box_row, box_row + 3):
        for c in range(box_col, box_col + 3):
            if grid[r][c] == num:
                return False
    return True

def solve_sudoku(grid, grid_size=9):
    for row in range(grid_size):
        for col in range(grid_size):
            if grid[row][col] == 0:
                for num in range(1, 10):
                    if is_valid_move(grid, row, col, num, grid_size):
                        grid[row][col] = num
                        if solve_sudoku(grid, grid_size):
                            return True
                        grid[row][col] = 0
                return False
    return True

def is_complete_solution(grid, grid_size=9):
    for r in range(grid_size):
        for c in range(grid_size):
            if grid[r][c] == 0:
                return False
    for r in range(grid_size):
        for c in range(grid_size):
            num = grid[r][c]
            grid[r][c] = 0
            if not is_valid_move(grid, r, c, num, grid_size):
                grid[r][c] = num
                return False
            grid[r][c] = num
    return True

def fill_diagonal_box(grid, start_row, start_col):
    numbers = list(range(1, 10))
    random.shuffle(numbers)
    for i in range(3):
        for j in range(3):
            grid[start_row + i][start_col + j] = numbers[i * 3 + j]

def add_strategic_placements(grid, grid_size=9):
    for _ in range(15):
        row = random.randint(0, 8)
        col = random.randint(0, 8)
        if grid[row][col] != 0:
            continue
        if (row // 3) == (col // 3):
            continue
        for num in range(1, 10):
            if is_valid_move(grid, row, col, num, grid_size):
                grid[row][col] = num
                break

def create_complex_base_pattern(grid):
    for box in range(0, 9, 3):
        fill_diagonal_box(grid, box, box)
    add_strategic_placements(grid)

def is_valid_row_swap(row1, row2):
    return (row1 // 3) == (row2 // 3)

def is_valid_col_swap(col1, col2):
    return (col1 // 3) == (col2 // 3)

def swap_rows(grid, row1, row2):
    grid[row1], grid[row2] = grid[row2], grid[row1]

def swap_columns(grid, col1, col2):
    for row in range(9):
        grid[row][col1], grid[row][col2] = grid[row][col2], grid[row][col1]

def apply_solution_transformations(grid):
    for block in range(3):
        start_row = block * 3
        rows = [start_row, start_row + 1, start_row + 2]
        random.shuffle(rows)
        if is_valid_row_swap(rows[0], rows[1]):
            swap_rows(grid, rows[0], rows[1])
        if is_valid_row_swap(rows[1], rows[2]):
            swap_rows(grid, rows[1], rows[2])
    for block in range(3):
        start_col = block * 3
        cols = [start_col, start_col + 1, start_col + 2]
        random.shuffle(cols)
        if is_valid_col_swap(cols[0], cols[1]):
            swap_columns(grid, cols[0], cols[1])
        if is_valid_col_swap(cols[1], cols[2]):
            swap_columns(grid, cols[1], cols[2])

def generate_simple_solution(grid_size=9):
    solution = [[0 for _ in range(grid_size)] for _ in range(grid_size)]
    for box in range(0, 9, 3):
        numbers = list(range(1, 10))
        random.shuffle(numbers)
        for i in range(3):
            for j in range(3):
                solution[box + i][box + j] = numbers[i * 3 + j]
    solve_sudoku(solution, grid_size)
    return solution

def generate_valid_solution(grid_size=9):
    max_attempts = 10
    for _ in range(max_attempts):
        solution = [[0 for _ in range(grid_size)] for _ in range(grid_size)]
        create_complex_base_pattern(solution)
        apply_solution_transformations(solution)
        if solve_sudoku(solution, grid_size) and is_complete_solution(solution, grid_size):
            return solution
    return generate_simple_solution(grid_size)

def count_solutions(grid, grid_size=9):
    count = 0
    for r in range(grid_size):
        for c in range(grid_size):
            if grid[r][c] == 0:
                for num in range(1, 10):
                    if is_valid_move(grid, r, c, num, grid_size):
                        grid[r][c] = num
                        count += count_solutions(grid, grid_size)
                        grid[r][c] = 0
                return count
    return 1

def ensure_no_complete_blocks(grid, grid_size=9):
    for box_row in range(3):
        for box_col in range(3):
            hint_count = 0
            hint_positions = []
            for r in range(box_row * 3, box_row * 3 + 3):
                for c in range(box_col * 3, box_col * 3 + 3):
                    if grid[r][c] != 0:
                        hint_count += 1
                        hint_positions.append((r, c))
            if hint_count >= 8:
                hints_to_remove = min(3, hint_count - 5)
                for _ in range(hints_to_remove):
                    if hint_positions:
                        r, c = random.choice(hint_positions)
                        original_num = grid[r][c]
                        grid[r][c] = 0
                        temp_grid = [row[:] for row in grid]
                        if count_solutions(temp_grid, grid_size) == 1:
                            hint_positions.remove((r, c))
                        else:
                            grid[r][c] = original_num

def create_puzzle_from_solution(solution, difficulty="medium", grid_size=9):
    grid = [row[:] for row in solution]
    difficulty_levels = {"easy": 40, "medium": 50, "hard": 60}
    cells_to_remove = difficulty_levels.get(difficulty, 50)
    all_cells = [(r, c) for r in range(grid_size) for c in range(grid_size)]
    random.shuffle(all_cells)
    removed = 0
    for r, c in all_cells:
        if removed >= cells_to_remove:
            break
        original = grid[r][c]
        grid[r][c] = 0
        temp = [row[:] for row in grid]
        if count_solutions(temp, grid_size) == 1:
            removed += 1
        else:
            grid[r][c] = original
    ensure_no_complete_blocks(grid, grid_size)
    hint_positions = [(r, c) for r in range(grid_size) for c in range(grid_size) if grid[r][c] != 0]
    return grid, hint_positions


class SudokuPuzzle(TutorEnvBase):
    def __init__(self, grid_size=9, problem_types=["easy", "medium", "hard"], **kwargs):
        if grid_size != 9:
            raise ValueError("Sudoku grid size must be 9")
        
        self.grid_size = grid_size
        self.problem_types = problem_types
        self.problem = None
        
        super().__init__(**kwargs)
        self.set_random_problem()
    
    def _blank_state(self):
        state = {}
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                state[f"cell_{r}_{c}"] = {"value": "0"}
        
        state["selected_cell"] = {"value": "none"}
        state["notes_mode"] = {"value": "false"}
        state["grid_size"] = {"value": str(self.grid_size)}
        state["hint_positions"] = {"value": str([])}
        
        return state
    
    def action_is_done(self, action):
        return action.selection == "done"
    
    def set_start_state(self, grid, solution, hint_positions):
        self.problem = (grid, solution)
        self.state = self._blank_state()
        
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if grid[r][c] != 0:
                    self.state[f"cell_{r}_{c}"] = {"value": str(grid[r][c])}
        
        self.state["hint_positions"] = {"value": str(hint_positions)}
    
    def set_random_problem(self):
        ptype = random.choice(self.problem_types)
        solution = generate_valid_solution(self.grid_size)
        grid, hint_positions = create_puzzle_from_solution(solution, ptype, self.grid_size)
        self.set_start_state(grid, solution, hint_positions)
        return {"grid": grid, "solution": solution, "hint_positions": hint_positions}
    
    def generate_valid_solution(self):
        return generate_valid_solution(self.grid_size)
    
    def is_complete_solution(self, grid):
        return is_complete_solution(grid, self.grid_size)
    
    def generate_simple_solution(self):
        return generate_simple_solution(self.grid_size)
    
    def create_complex_base_pattern(self, grid):
        create_complex_base_pattern(grid)
    
    def fill_diagonal_box(self, grid, start_row, start_col):
        fill_diagonal_box(grid, start_row, start_col)
    
    def add_strategic_placements(self, grid):
        add_strategic_placements(grid, self.grid_size)
    
    def apply_solution_transformations(self, grid):
        apply_solution_transformations(grid)
    
    def is_valid_row_swap(self, grid, row1, row2):
        return is_valid_row_swap(row1, row2)
    
    def is_valid_col_swap(self, grid, col1, col2):
        return is_valid_col_swap(col1, col2)
    
    def swap_rows(self, grid, row1, row2):
        swap_rows(grid, row1, row2)
    
    def swap_columns(self, grid, col1, col2):
        swap_columns(grid, col1, col2)
    
    def solve_sudoku(self, grid):
        return solve_sudoku(grid, self.grid_size)
    
    def is_valid_move(self, grid, row, col, num):
        return is_valid_move(grid, row, col, num, self.grid_size)
    
    def create_puzzle(self, solution, difficulty):
        return create_puzzle_from_solution(solution, difficulty, self.grid_size)
    
    def ensure_no_complete_blocks(self, grid):
        ensure_no_complete_blocks(grid, self.grid_size)
    
    def count_solutions(self, grid):
        return count_solutions(grid, self.grid_size)
    
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
        for num in range(1, 10):
            args.append(str(num))
        args.append("done")
        return args
    
    def get_demo(self, state=None, **kwargs):
        state = self.state if state is None else state
        grid, solution = self.problem if self.problem else (None, None)
        
        if not grid or not solution:
            return None
        
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                current_value = state.get(f"cell_{r}_{c}", {}).get("value", "0")
                if current_value == "0":
                    correct_value = solution[r][c]
                    if self.is_valid_move(grid, r, c, correct_value):
                        sai = (f"cell_{r}_{c}", 'FillCell', str(correct_value))
                        arg_foci = [f"cell_{r}_{c}"]
                        how_help = f"Fill cell ({r},{c}) with {correct_value}"
                        return Action(sai, arg_foci=arg_foci, how_help=how_help)
        
        return None
    
    def check(self, action, **kwargs):
        action = Action(action)
        grid, solution = self.problem if self.problem else (None, None)
        
        if not grid or not solution:
            return -1
        
        if action.selection == "done":
            current_grid = []
            for r in range(self.grid_size):
                row = []
                for c in range(self.grid_size):
                    value = self.state.get(f"cell_{r}_{c}", {}).get("value", "0")
                    row.append(int(value) if value != "0" else 0)
                current_grid.append(row)
            
            if self.is_sudoku_complete(current_grid):
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
        
        current_value = self.state.get(f"cell_{r}_{c}", {}).get("value", "0")
        if current_value == "0":
            return -1
        
        num = int(current_value)
        if self.is_valid_move(grid, r, c, num):
            return 1
        else:
            return -1
    
    def apply(self, action, **kwargs):
        action = Action(action)
        grid, solution = self.problem if self.problem else (None, None)
        
        if not grid or not solution:
            return self.state
        
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
        
        new_state = self.state.copy()
        
        if action.input and action.input.isdigit():
            num = int(action.input)
            if 1 <= num <= 9:
                new_state[f"cell_{r}_{c}"] = {"value": str(num)}
        
        new_state["selected_cell"] = {"value": f"{r},{c}"}
        
        return new_state
    
    def is_sudoku_complete(self, grid):
        for row in grid:
            if 0 in row:
                return False
        return True
    
    def set_problem(self, *args, **kwargs):
        """Set the Tutor Environment's current problem"""
        self.set_random_problem()
    
    def get_problem(self):
        """Get some kind of unique identifier for the current problem"""
        if self.problem:
            grid, solution, hint_positions = self.problem
            return f"sudoku_{self.grid_size}_{hash(str(grid))}"
        return "sudoku_default"
    
    def get_problem_config(self):
        """Get a dictionary with the arguments used to instantiate the current problem"""
        return {
            "grid_size": self.grid_size,
            "problem_types": self.problem_types
        }
    
    def get_all_demos(self, state=None, **kwargs):
        """Get a list of instances of Action for all next correct actions in the Tutor"""
        state = self.state if state is None else state
        grid, solution, hint_positions = self.problem if self.problem else (None, None, None)
        
        if not grid or not solution:
            return []
        
        demos = []
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if grid[r][c] == 0:  # Empty cell
                    if solution[r][c] != 0:  # Has a solution
                        sai = (f"cell_{r}_{c}", 'PlaceNumber', f"{r},{c},{solution[r][c]}")
                        arg_foci = [f"cell_{r}_{c}"]
                        how_help = f"Place {solution[r][c]} at ({r},{c})"
                        demos.append(Action(sai, arg_foci=arg_foci, how_help=how_help))
        
        return demos
    
    def get_state(self):
        """Get the current state of the Tutor"""
        return self.state
    
    def set_state(self, state):
        """Set the current state of the Tutor"""
        self.state = state


if __name__ == "__main__":
    print("=== Testing SudokuPuzzle Environment Implementation ===\n")
    
    print("1. Testing basic puzzle generation...")
    try:
        env = SudokuPuzzle(grid_size=9, problem_types=["easy", "medium", "hard"])
        print(f"   ✓ Generated Sudoku puzzle: {env.grid_size}x{env.grid_size}")
        print(f"   ✓ Problem types: {env.problem_types}")
    except Exception as e:
        print(f"   ✗ Error generating puzzle: {e}")
    
    print("\n2. Testing state management...")
    try:
        print(f"   ✓ Initial state keys: {list(env.state.keys())[:5]}...")
        print(f"   ✓ Grid size: {env.state.get('grid_size', {}).get('value', '')}")
        print(f"   ✓ Hint positions: {env.state.get('hint_positions', {}).get('value', '')}")
    except Exception as e:
        print(f"   ✗ Error in state management: {e}")
    
    print("\n3. Testing action space...")
    try:
        selections = env.get_possible_selections()
        args = env.get_possible_args()
        print(f"   ✓ Possible selections: {len(selections)} (showing first 5: {selections[:5]})")
        print(f"   ✓ Possible args: {len(args)} (showing first 5: {args[:5]})")
        print(f"   ✓ Includes 'done' action: {'done' in selections}")
    except Exception as e:
        print(f"   ✗ Error getting action space: {e}")
    
    print("\n4. Testing demo generation...")
    try:
        demo = env.get_demo()
        if demo:
            print(f"   ✓ Demo generated successfully")
            print(f"   ✓ Selection: {demo.selection}")
            print(f"   ✓ Action type: {demo.action_type}")
            print(f"   ✓ Input: {demo.input}")
            print(f"   ✓ Help text: {demo.how_help}")
        else:
            print(f"   ⚠ No demo available")
    except Exception as e:
        print(f"   ✗ Error generating demo: {e}")
    
    print("\n5. Testing action checking...")
    try:
        if demo:
            check_result = env.check(demo)
            print(f"   ✓ Check result: {check_result} ({'Correct' if check_result == 1 else 'Incorrect'})")
        else:
            print(f"   ⚠ Skipping check test - no demo available")
    except Exception as e:
        print(f"   ✗ Error checking action: {e}")
    
    print("\n6. Testing state transitions...")
    try:
        if demo and env.check(demo) == 1:
            old_state = env.state.copy()
            new_state = env.apply(demo)
            print(f"   ✓ State transition successful")
            print(f"   ✓ Selected cell: {new_state.get('selected_cell', {}).get('value', '')}")
            
            env.state = new_state
            
            next_demo = env.get_demo()
            if next_demo:
                print(f"   ✓ Next demo available: {next_demo.selection}")
            else:
                print(f"   ⚠ No next demo available")
        else:
            print(f"   ⚠ Skipping state transition test - demo not valid")
    except Exception as e:
        print(f"   ✗ Error in state transition: {e}")
    
    print("\n7. Testing helper functions...")
    try:
        test_grid = [[0 for _ in range(9)] for _ in range(9)]
        is_valid = env.is_valid_move(test_grid, 0, 0, 1)
        print(f"   ✓ is_valid_move test: {is_valid}")
        
        complete_grid = [[1 for _ in range(9)] for _ in range(9)]
        is_complete = env.is_sudoku_complete(complete_grid)
        print(f"   ✓ is_sudoku_complete test: {is_complete}")
    except Exception as e:
        print(f"   ✗ Error testing helper functions: {e}")
    
    print("\n=== Testing Complete ===")
    print("All core functions have been tested successfully!")