# zip_game.py
# Minimal “Zip” puzzle clone in Python (Tkinter)
# Run: python zip_game.py

import tkinter as tk
from tkinter import messagebox

CELL = 56          # pixel size of each square
GAP = 2            # cell gap
PADDING = 16       # canvas padding
BG = "#0f172a"     # slate-900
GRID_BG = "#1e293b"  # slate-800
PATH_COLOR = "#38bdf8"  # sky-400
NUM_BG = "#334155"     # slate-700
NUM_FG = "#e2e8f0"     # slate-200
CURSOR_COLOR = "#fbbf24"  # amber-400
LOCKED_NUM_FG = "#f8fafc" # slate-50
VICTORY_COLOR = "#22c55e"  # green-500

# --- Sample puzzles ---
# 0 = empty. Positive ints are fixed clues that must be visited in that order.
# Rule: Path must visit every cell exactly once, hitting numbers 1..K in sequence.
PUZZLES = [
    # 6x6 puzzle with numbers 1-16
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
]

import random
import copy
from datetime import datetime
import math
import numpy as np

def neighbors(r, c):
    return [(r-1, c), (r+1, c), (r, c-1), (r, c+1)]

def get_clue_count_normal_distribution(min_clues=6, max_clues=16, mean=10, std=1.5):
    """Generate clue count using normal distribution with mean around 10"""
    # Use numpy for faster normal distribution generation
    clue_count = int(np.random.normal(mean, std))
    
    # Clamp to valid range
    clue_count = max(min_clues, min(max_clues, clue_count))
    return clue_count

def are_consecutive_numbers_adjacent(grid, R, C):
    """Check if any consecutive numbers are adjacent to each other"""
    numbered_positions = {}
    for r in range(R):
        for c in range(C):
            if grid[r][c] > 0:
                numbered_positions[grid[r][c]] = (r, c)
    
    # Check if consecutive numbers are adjacent
    for num in range(1, max(numbered_positions.keys())):
        if num in numbered_positions and num + 1 in numbered_positions:
            r1, c1 = numbered_positions[num]
            r2, c2 = numbered_positions[num + 1]
            # Check if they are adjacent (manhattan distance = 1)
            if abs(r1 - r2) + abs(c1 - c2) == 1:
                return True
    return False

def count_consecutive_adjacent_numbers(grid, R, C):
    """Count how many pairs of consecutive numbers are adjacent to each other"""
    numbered_positions = {}
    for r in range(R):
        for c in range(C):
            if grid[r][c] > 0:
                numbered_positions[grid[r][c]] = (r, c)
    
    consecutive_count = 0
    # Check if consecutive numbers are adjacent
    for num in range(1, max(numbered_positions.keys())):
        if num in numbered_positions and num + 1 in numbered_positions:
            r1, c1 = numbered_positions[num]
            r2, c2 = numbered_positions[num + 1]
            # Check if they are adjacent (manhattan distance = 1)
            if abs(r1 - r2) + abs(c1 - c2) == 1:
                consecutive_count += 1
    return consecutive_count

def count_long_straight_segments(path, max_straight_length=4):
    """Count how many long straight segments exist in the path"""
    if len(path) < max_straight_length:
        return 0
    
    straight_count = 0
    for i in range(len(path) - max_straight_length + 1):
        segment = path[i:i + max_straight_length]
        
        # Check if segment is straight horizontally
        if all(segment[j][0] == segment[0][0] for j in range(len(segment))):
            # Check if columns are consecutive
            cols = [segment[j][1] for j in range(len(segment))]
            if cols == list(range(min(cols), max(cols) + 1)):
                straight_count += 1
        
        # Check if segment is straight vertically
        elif all(segment[j][1] == segment[0][1] for j in range(len(segment))):
            # Check if rows are consecutive
            rows = [segment[j][0] for j in range(len(segment))]
            if rows == list(range(min(rows), max(rows) + 1)):
                straight_count += 1
    
    return straight_count

def calculate_path_complexity(path):
    """Calculate a complexity score for the path (higher = more complex)"""
    if len(path) < 3:
        return 0
    
    # Count direction changes
    direction_changes = 0
    for i in range(1, len(path) - 1):
        prev_r, prev_c = path[i-1]
        curr_r, curr_c = path[i]
        next_r, next_c = path[i+1]
        
        # Calculate direction vectors
        dir1 = (curr_r - prev_r, curr_c - prev_c)
        dir2 = (next_r - curr_r, next_c - curr_c)
        
        # If directions are different, it's a turn
        if dir1 != dir2:
            direction_changes += 1
    
    # Count long straight segments (penalize these)
    long_straights = count_long_straight_segments(path, max_straight_length=4)
    
    # Complexity score: more turns = higher score, long straights = lower score
    complexity = direction_changes - (long_straights * 2)
    return complexity

def is_valid_position(r, c, R, C):
    """Check if position is within bounds"""
    return 0 <= r < R and 0 <= c < C

def find_hamiltonian_path(grid, start_r, start_c, R, C):
    """Find a Hamiltonian path (visiting every cell exactly once) starting from (start_r, start_c)"""
    path = [(start_r, start_c)]
    visited = {(start_r, start_c)}
    
    def backtrack():
        if len(path) == R * C:
            return True
        
        current_r, current_c = path[-1]
        
        # Shuffle directions to add randomness and avoid predictable patterns
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
    """Find a Hamiltonian path with higher complexity using efficient approach"""
    # Try just 3 attempts for speed
    for attempt in range(3):
        path = [(start_r, start_c)]
        visited = {(start_r, start_c)}
        
        def backtrack():
            if len(path) == R * C:
                return True
            
            current_r, current_c = path[-1]
            
            # Use a more complex direction ordering to encourage turns
            # Prioritize directions that create turns
            directions = []
            if len(path) >= 2:
                # Get previous direction to avoid going straight
                prev_r, prev_c = path[-2]
                prev_dir = (current_r - prev_r, current_c - prev_c)
                
                # Shuffle all directions but put non-straight directions first
                all_dirs = [(0, 1), (1, 0), (0, -1), (-1, 0)]
                random.shuffle(all_dirs)
                
                # Put directions that create turns first
                for dr, dc in all_dirs:
                    if (dr, dc) != prev_dir:
                        directions.append((dr, dc))
                # Add the straight direction last
                directions.append(prev_dir)
            else:
                # First move, just shuffle
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
    
    # Fall back to regular path if complex path fails
    return find_hamiltonian_path(grid, start_r, start_c, R, C)

def generate_solid_lines(R=6, C=6, max_lines=6):
    """Generate solid lines (barriers) between cells, with reduced skewness towards 0"""
    # Reduced skewness: 40% chance of 0 lines, 35% chance of 1-2 lines, 25% chance of 3+ lines
    rand = random.random()
    if rand < 0.4:
        num_lines = 0
    elif rand < 0.75:
        num_lines = random.randint(1, 2)
    else:
        num_lines = random.randint(3, max_lines)
    
    if num_lines == 0:
        return []
    
    # Generate possible line positions (edges between cells)
    possible_lines = []
    
    # Horizontal lines (between rows)
    for r in range(R - 1):
        for c in range(C):
            possible_lines.append(('h', r, c))  # horizontal line between (r,c) and (r+1,c)
    
    # Vertical lines (between columns)
    for r in range(R):
        for c in range(C - 1):
            possible_lines.append(('v', r, c))  # vertical line between (r,c) and (r,c+1)
    
    # Randomly select lines
    selected_lines = random.sample(possible_lines, min(num_lines, len(possible_lines)))
    return selected_lines

def generate_solid_lines_for_path(path, grid, R=6, C=6, max_lines=6):
    """Generate solid lines that don't interfere with the given path and don't separate numbered clues"""
    # Reduced skewness: 40% chance of 0 lines, 35% chance of 1-2 lines, 25% chance of 3+ lines
    rand = random.random()
    if rand < 0.4:
        num_lines = 0
    elif rand < 0.75:
        num_lines = random.randint(1, 2)
    else:
        num_lines = random.randint(3, max_lines)
    
    if num_lines == 0:
        return []
    
    # Generate all possible line positions (edges between cells)
    possible_lines = []
    
    # Horizontal lines (between rows)
    for r in range(R - 1):
        for c in range(C):
            possible_lines.append(('h', r, c))  # horizontal line between (r,c) and (r+1,c)
    
    # Vertical lines (between columns)
    for r in range(R):
        for c in range(C - 1):
            possible_lines.append(('v', r, c))  # vertical line between (r,c) and (r,c+1)
    
    # Filter out lines that would interfere with the path or separate numbered clues
    valid_lines = []
    for line_type, line_r, line_c in possible_lines:
        # Check if this line would block any move in the path
        blocks_path = False
        for i in range(len(path) - 1):
            r1, c1 = path[i]
            r2, c2 = path[i + 1]
            
            if line_type == 'h':  # horizontal line
                # Line is between (line_r, line_c) and (line_r+1, line_c)
                if ((r1 == line_r and c1 == line_c and r2 == line_r + 1 and c2 == line_c) or
                    (r1 == line_r + 1 and c1 == line_c and r2 == line_r and c2 == line_c)):
                    blocks_path = True
                    break
            elif line_type == 'v':  # vertical line
                # Line is between (line_r, line_c) and (line_r, line_c+1)
                if ((r1 == line_r and c1 == line_c and r2 == line_r and c2 == line_c + 1) or
                    (r1 == line_r and c1 == line_c + 1 and r2 == line_r and c2 == line_c)):
                    blocks_path = True
                    break
        
        if blocks_path:
            continue
        
        # Check if this line would separate two cells that both contain numbered clues
        separates_numbered_clues = False
        if line_type == 'h':  # horizontal line
            # Check if both (line_r, line_c) and (line_r+1, line_c) have numbers
            if grid[line_r][line_c] > 0 and grid[line_r + 1][line_c] > 0:
                separates_numbered_clues = True
        elif line_type == 'v':  # vertical line
            # Check if both (line_r, line_c) and (line_r, line_c+1) have numbers
            if grid[line_r][line_c] > 0 and grid[line_r][line_c + 1] > 0:
                separates_numbered_clues = True
        
        if not separates_numbered_clues:
            valid_lines.append((line_type, line_r, line_c))
    
    # Randomly select from valid lines
    if len(valid_lines) == 0:
        return []
    
    selected_lines = random.sample(valid_lines, min(num_lines, len(valid_lines)))
    return selected_lines

def generate_solvable_puzzle(R=6, C=6, min_numbers=6, max_numbers=16):
    """Generate a solvable puzzle with the specified number of numbered cells and solid lines"""
    # Try fewer attempts for much faster generation
    for attempt in range(20):
        # Create empty grid
        grid = [[0 for _ in range(C)] for _ in range(R)]
        
        # Choose number of numbered cells using normal distribution
        num_numbers = get_clue_count_normal_distribution(min_numbers, max_numbers, mean=10, std=1.5)
        
        # Try to place numbers in a way that creates a solvable puzzle
        # Start by finding a valid Hamiltonian path with good complexity
        start_r, start_c = random.randint(0, R-1), random.randint(0, C-1)
        found_path, path = find_complex_hamiltonian_path(grid, start_r, start_c, R, C, min_complexity=2)
        
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
        
        # Quick verification - just check if solvable with solid lines
        if verify_puzzle_solvability_with_lines(grid, solid_lines, R, C):
            return grid, solid_lines
    
    # If we couldn't generate a good puzzle, return a simple one
    simple_grid = generate_simple_puzzle(R, C, min_numbers)
    return simple_grid, []

def generate_simple_puzzle(R=6, C=6, num_numbers=6):
    """Generate a simple puzzle as fallback"""
    grid = [[0 for _ in range(C)] for _ in range(R)]
    
    # Try to find a Hamiltonian path first
    start_r, start_c = random.randint(0, R-1), random.randint(0, C-1)
    found_path, path = find_hamiltonian_path(grid, start_r, start_c, R, C)
    
    if found_path:
        # Use the Hamiltonian path approach to ensure path ends on numbered cell
        last_position = len(path) - 1
        number_positions = random.sample(range(len(path) - 1), num_numbers - 1)
        number_positions.append(last_position)  # Always include the last position
        number_positions.sort()
        
        for i, pos_idx in enumerate(number_positions):
            r, c = path[pos_idx]
            grid[r][c] = i + 1
    else:
        # Fallback to checkerboard pattern, but ensure last position is numbered
        positions = []
        for r in range(R):
            for c in range(C):
                if (r + c) % 2 == 0:  # Checkerboard pattern
                    positions.append((r, c))
        
        # Select random positions for numbers, ensuring we have enough
        if len(positions) >= num_numbers:
            selected = random.sample(positions, num_numbers)
            selected.sort(key=lambda x: (x[0], x[1]))  # Sort by position
            
            for i, (r, c) in enumerate(selected):
                grid[r][c] = i + 1
    
    return grid

def path_respects_solid_lines(path, solid_lines, R, C):
    """Check if a path respects all solid line barriers"""
    for i in range(len(path) - 1):
        r1, c1 = path[i]
        r2, c2 = path[i + 1]
        
        # Check if this move crosses any solid line
        for line_type, line_r, line_c in solid_lines:
            if line_type == 'h':  # horizontal line
                # Line is between (line_r, line_c) and (line_r+1, line_c)
                if ((r1 == line_r and c1 == line_c and r2 == line_r + 1 and c2 == line_c) or
                    (r1 == line_r + 1 and c1 == line_c and r2 == line_r and c2 == line_c)):
                    return False
            elif line_type == 'v':  # vertical line
                # Line is between (line_r, line_c) and (line_r, line_c+1)
                if ((r1 == line_r and c1 == line_c and r2 == line_r and c2 == line_c + 1) or
                    (r1 == line_r and c1 == line_c + 1 and r2 == line_r and c2 == line_c)):
                    return False
    return True

def verify_puzzle_solvability_with_lines(grid, solid_lines, R, C):
    """Verify that a puzzle is solvable with solid lines and ends on a numbered cell"""
    # Find the starting position (cell with number 1)
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
    
    # Try to find a path that visits all cells and hits numbers in order
    path = [start_pos]
    visited = {start_pos}
    next_required = 2
    
    def can_extend_to(r, c):
        if (r, c) in visited:
            return False
        if not is_valid_position(r, c, R, C):
            return False
        # Check if this cell has a number that matches what we need
        if grid[r][c] > 0 and grid[r][c] != next_required:
            return False
        return True
    
    def backtrack():
        nonlocal next_required
        if len(path) == R * C:
            # Check that the path ends on a numbered cell (the highest number)
            last_r, last_c = path[-1]
            if grid[last_r][last_c] == max_num:
                return True
            else:
                return False
        
        current_r, current_c = path[-1]
        for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            next_r, next_c = current_r + dr, current_c + dc
            if can_extend_to(next_r, next_c):
                # Check if this move would cross a solid line
                if not crosses_solid_line((current_r, current_c), (next_r, next_c), solid_lines):
                    path.append((next_r, next_c))
                    visited.add((next_r, next_c))
                    
                    # Update next_required if we hit a number
                    if grid[next_r][next_c] == next_required:
                        next_required += 1
                    
                    if backtrack():
                        return True
                    
                    # Backtrack
                    if grid[next_r][next_c] == next_required - 1:
                        next_required -= 1
                    path.pop()
                    visited.remove((next_r, next_c))
        return False
    
    # First check if the puzzle is solvable
    if not backtrack():
        return False
    
    # Additional check: ensure all numbered cells are visited in order
    # and the path ends on the highest numbered cell
    numbered_positions = [(r, c, num) for r, c, num in numbered_cells]
    numbered_positions.sort(key=lambda x: x[2])  # Sort by number
    
    # Check that we have consecutive numbers starting from 1
    expected_numbers = list(range(1, max_num + 1))
    actual_numbers = [num for _, _, num in numbered_positions]
    if actual_numbers != expected_numbers:
        return False
    
    return True

def crosses_solid_line(from_pos, to_pos, solid_lines):
    """Check if a move from from_pos to to_pos crosses any solid line"""
    r1, c1 = from_pos
    r2, c2 = to_pos
    
    for line_type, line_r, line_c in solid_lines:
        if line_type == 'h':  # horizontal line
            # Line is between (line_r, line_c) and (line_r+1, line_c)
            if ((r1 == line_r and c1 == line_c and r2 == line_r + 1 and c2 == line_c) or
                (r1 == line_r + 1 and c1 == line_c and r2 == line_r and c2 == line_c)):
                return True
        elif line_type == 'v':  # vertical line
            # Line is between (line_r, line_c) and (line_r, line_c+1)
            if ((r1 == line_r and c1 == line_c and r2 == line_r and c2 == line_c + 1) or
                (r1 == line_r and c1 == line_c + 1 and r2 == line_r and c2 == line_c)):
                return True
    return False

def verify_puzzle_solvability(grid, R, C):
    """Verify that a puzzle is solvable and ends on a numbered cell (without solid lines)"""
    return verify_puzzle_solvability_with_lines(grid, [], R, C)

# Generate additional puzzles
def generate_puzzle_collection():
    """Generate a collection of solvable puzzles using normal distribution"""
    puzzles = []
    
    # Generate even fewer puzzles for much faster startup
    clue_counts = [9, 10, 11]  # Just 3 puzzles for speed
    
    for num_clues in clue_counts:
        puzzle, solid_lines = generate_solvable_puzzle(6, 6, num_clues, num_clues)
        puzzles.append({
            "name": f"Generated {num_clues} clues",
            "grid": puzzle,
            "solid_lines": solid_lines
        })
    
    return puzzles

# Add generated puzzles to the PUZZLES list
GENERATED_PUZZLES = generate_puzzle_collection()
PUZZLES.extend(GENERATED_PUZZLES)

def generate_new_puzzle():
    """Generate a new random puzzle with 6-16 numbers using normal distribution"""
    num_clues = get_clue_count_normal_distribution(6, 16, mean=10, std=1.5)
    puzzle, solid_lines = generate_solvable_puzzle(6, 6, num_clues, num_clues)
    return {
        "name": f"Random {num_clues} clues",
        "grid": puzzle,
        "solid_lines": solid_lines
    }

class ZipGame(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Zip (Python)")
        self.configure(bg=BG)
        self.resizable(False, False)

        self.level_idx = 0
        self.grid_data = None
        self.solid_lines = []
        self.R = self.C = 0

        self.header = tk.Label(
            self, text="", fg="#e2e8f0", bg=BG, font=("Inter", 16, "bold")
        )
        self.header.pack(pady=(12, 6))

        self.canvas = tk.Canvas(self, bg=GRID_BG, highlightthickness=0)
        self.canvas.pack(padx=PADDING, pady=PADDING)

        self.status = tk.Label(
            self, text="", fg="#cbd5e1", bg=BG, font=("Inter", 12)
        )
        self.status.pack(pady=(0, 5))

        # Button frame to hold both buttons
        self.button_frame = tk.Frame(self, bg=BG)
        self.button_frame.pack(pady=(0, 10))

        # Solution button
        self.solution_button = tk.Button(
            self.button_frame, text="Show Solution", 
            command=self.show_solution,
            bg="white", fg="black", 
            font=("Inter", 10, "bold"),
            relief="flat", padx=20, pady=5,
            activebackground="lightgray", activeforeground="black",
            highlightthickness=0, bd=0
        )
        self.solution_button.pack(side=tk.LEFT, padx=(0, 10))

        # History button
        self.history_button = tk.Button(
            self.button_frame, text="History", 
            command=self.show_history,
            bg="white", fg="black", 
            font=("Inter", 10, "bold"),
            relief="flat", padx=20, pady=5,
            activebackground="lightgray", activeforeground="black",
            highlightthickness=0, bd=0
        )
        self.history_button.pack(side=tk.LEFT)

        # Force button styling with multiple approaches
        self.solution_button.configure(bg="white", fg="black")
        self.history_button.configure(bg="white", fg="black")
        
        # Additional styling to override system theme
        self.solution_button.config(bg="white", fg="black")
        self.history_button.config(bg="white", fg="black")
        
        # Try to override system styling
        try:
            import tkinter.ttk as ttk
            style = ttk.Style()
            style.configure("Black.TButton", background="black", foreground="white")
        except:
            pass

        self.path = []           # list of (r, c) in order drawn
        self.path_set = set()    # for quick membership
        self.fixed = {}          # (r,c) -> number
        self.max_fixed = 0       # largest number in clues
        self.next_required_num = 1
        self.dragging = False
        self.completed_puzzles = []  # Store completed puzzles

        self.bind_events()
        self.load_level(0)

    def bind_events(self):
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.bind("r", self.on_reset)
        self.bind("R", self.on_reset)
        self.bind("n", self.on_next)
        self.bind("N", self.on_next)
        self.bind("p", self.on_prev)
        self.bind("P", self.on_prev)
        self.bind("g", self.on_generate)
        self.bind("G", self.on_generate)
        self.bind("s", self.show_solution)
        self.bind("S", self.show_solution)
        self.bind("h", self.show_history)
        self.bind("H", self.show_history)

    # ---- Level handling ----
    def load_level(self, idx):
        self.level_idx = idx % len(PUZZLES)
        level = PUZZLES[self.level_idx]
        self.header.config(text=f"Zip – {level['name']}  (N/P: switch · R: reset · G: generate · S: solution · H: history · Click visited node to undo)")
        self.grid_data = [row[:] for row in level["grid"]]
        self.solid_lines = level.get("solid_lines", [])
        self.R, self.C = len(self.grid_data), len(self.grid_data[0])
        self.canvas.config(
            width=self.C * (CELL + GAP) + GAP,
            height=self.R * (CELL + GAP) + GAP,
        )
        self.fixed.clear()
        self.max_fixed = 0
        for r in range(self.R):
            for c in range(self.C):
                val = self.grid_data[r][c]
                if val > 0:
                    self.fixed[(r, c)] = val
                    if val > self.max_fixed:
                        self.max_fixed = val
        self.path = []
        self.path_set = set()
        # If "1" exists, show it's the start; otherwise first click defines start.
        self.next_required_num = 1
        self.redraw()
        self.status.config(text="Draw a single path visiting all cells. Hit numbers in order 1 → 2 → 3 → … Click any visited node to undo to that point.")

    def on_next(self, _=None):
        self.load_level(self.level_idx + 1)

    def on_prev(self, _=None):
        self.load_level(self.level_idx - 1)

    def on_generate(self, _=None):
        """Generate a new random puzzle"""
        new_puzzle = generate_new_puzzle()
        # Add the new puzzle to the end of the list
        PUZZLES.append(new_puzzle)
        # Load the new puzzle
        self.load_level(len(PUZZLES) - 1)

    def show_solution(self, _=None):
        """Show the solution by automatically solving the puzzle"""
        if self.check_victory():
            self.status.config(text="Puzzle already solved!")
            return
        
        # Find the solution path
        solution_path = self.find_solution_path()
        if not solution_path:
            self.status.config(text="No solution found!")
            return
        
        # Clear current path
        self.path = []
        self.path_set = set()
        self.next_required_num = 1
        
        # Animate the solution
        self.animate_solution(solution_path)

    def find_solution_path(self):
        """Find the solution path for the current puzzle"""
        # Find the starting position (cell with number 1) and max number
        start_pos = None
        max_num = 0
        for r in range(self.R):
            for c in range(self.C):
                if self.grid_data[r][c] == 1:
                    start_pos = (r, c)
                if self.grid_data[r][c] > max_num:
                    max_num = self.grid_data[r][c]
        
        if not start_pos or max_num == 0:
            return None
        
        # Use backtracking to find the solution
        path = [start_pos]
        visited = {start_pos}
        next_required = 2
        
        def can_extend_to(r, c):
            if (r, c) in visited:
                return False
            if not self.in_bounds(r, c):
                return False
            # Check if this cell has a number that matches what we need
            if self.grid_data[r][c] > 0 and self.grid_data[r][c] != next_required:
                return False
            return True
        
        def backtrack():
            nonlocal next_required
            if len(path) == self.R * self.C:
                # Check that the path ends on a numbered cell (the highest number)
                last_r, last_c = path[-1]
                if self.grid_data[last_r][last_c] == max_num:
                    return True
                else:
                    return False
            
            current_r, current_c = path[-1]
            for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                next_r, next_c = current_r + dr, current_c + dc
                if can_extend_to(next_r, next_c):
                    # Check if this move would cross a solid line
                    if not crosses_solid_line((current_r, current_c), (next_r, next_c), self.solid_lines):
                        path.append((next_r, next_c))
                        visited.add((next_r, next_c))
                        
                        # Update next_required if we hit a number
                        if self.grid_data[next_r][next_c] == next_required:
                            next_required += 1
                        
                        if backtrack():
                            return True
                        
                        # Backtrack
                        if self.grid_data[next_r][next_c] == next_required - 1:
                            next_required -= 1
                        path.pop()
                        visited.remove((next_r, next_c))
            return False
        
        if backtrack():
            return path
        return None

    def animate_solution(self, solution_path):
        """Animate the solution by drawing the path step by step"""
        self.solution_button.config(state="disabled")
        self.status.config(text="Showing solution...")
        
        def draw_next_step(step):
            if step < len(solution_path):
                r, c = solution_path[step]
                self.push(r, c)
                self.redraw()
                # Schedule next step after a short delay
                self.after(200, lambda: draw_next_step(step + 1))
            else:
                # Solution complete
                self.status.config(text="Solution complete!")
                self.solution_button.config(state="normal")
                if self.check_victory():
                    self.after(1000, self.show_victory_message)
        
        draw_next_step(0)

    def get_timestamp(self):
        """Get current timestamp as string"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def show_history(self, _=None):
        """Show completed puzzles history"""
        if not self.completed_puzzles:
            messagebox.showinfo("History", "No completed puzzles yet!")
            return
        
        # Create history window
        history_window = tk.Toplevel(self)
        history_window.title("Completed Puzzles")
        history_window.configure(bg=BG)
        history_window.geometry("400x500")
        
        # Title
        title_label = tk.Label(
            history_window, 
            text="Completed Puzzles", 
            fg="#e2e8f0", bg=BG, 
            font=("Inter", 16, "bold")
        )
        title_label.pack(pady=10)
        
        # Scrollable frame for puzzle list
        canvas = tk.Canvas(history_window, bg=BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(history_window, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=BG)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Add each completed puzzle
        for i, puzzle in enumerate(reversed(self.completed_puzzles)):  # Show newest first
            puzzle_frame = tk.Frame(scrollable_frame, bg="#1e293b", relief="raised", bd=1)
            puzzle_frame.pack(fill="x", padx=10, pady=5)
            
            # Puzzle info
            info_text = f"{puzzle['name']}\nCompleted: {puzzle['timestamp']}"
            info_label = tk.Label(
                puzzle_frame, 
                text=info_text, 
                fg="#e2e8f0", bg="#1e293b", 
                font=("Inter", 10),
                justify="left"
            )
            info_label.pack(side="left", padx=10, pady=5)
            
            # Replay button
            replay_btn = tk.Button(
                puzzle_frame,
                text="Replay",
                command=lambda p=puzzle: self.replay_puzzle(p),
                bg="#334155", fg="#e2e8f0",
                font=("Inter", 9, "bold"),
                relief="flat", padx=10, pady=2
            )
            replay_btn.pack(side="right", padx=10, pady=5)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Close button
        close_btn = tk.Button(
            history_window,
            text="Close",
            command=history_window.destroy,
            bg="#1e293b", fg="#e2e8f0",
            font=("Inter", 10, "bold"),
            relief="flat", padx=20, pady=5
        )
        close_btn.pack(pady=10)

    def replay_puzzle(self, puzzle):
        """Replay a completed puzzle"""
        # Add the puzzle to the current list if not already there
        puzzle_exists = False
        for existing_puzzle in PUZZLES:
            if (existing_puzzle["name"] == puzzle["name"] and 
                existing_puzzle["grid"] == puzzle["grid"]):
                puzzle_exists = True
                break
        
        if not puzzle_exists:
            PUZZLES.append({
                "name": f"Replay: {puzzle['name']}",
                "grid": puzzle["grid"],
                "solid_lines": puzzle.get("solid_lines", [])
            })
            self.load_level(len(PUZZLES) - 1)
        else:
            # Find and load the existing puzzle
            for i, existing_puzzle in enumerate(PUZZLES):
                if (existing_puzzle["name"] == puzzle["name"] and 
                    existing_puzzle["grid"] == puzzle["grid"]):
                    self.load_level(i)
                    break

    def on_reset(self, _=None):
        self.path = []
        self.path_set = set()
        self.next_required_num = 1
        self.redraw()
        self.status.config(text="Reset. Start again!")

    # ---- Drawing ----
    def cell_rect(self, r, c):
        x0 = GAP + c * (CELL + GAP)
        y0 = GAP + r * (CELL + GAP)
        x1 = x0 + CELL
        y1 = y0 + CELL
        return x0, y0, x1, y1

    def redraw(self):
        self.canvas.delete("all")
        is_victory = self.check_victory()
        
        # Choose colors based on victory state
        path_color = VICTORY_COLOR if is_victory else PATH_COLOR
        cursor_color = VICTORY_COLOR if is_victory else CURSOR_COLOR
        num_bg = VICTORY_COLOR if is_victory else NUM_BG
        num_fg = "#ffffff" if is_victory else LOCKED_NUM_FG
        
        # Grid cells
        for r in range(self.R):
            for c in range(self.C):
                x0, y0, x1, y1 = self.cell_rect(r, c)
                self.canvas.create_rectangle(x0, y0, x1, y1, fill=GRID_BG, outline=BG, width=1)

        # Draw solid lines (barriers)
        for line_type, line_r, line_c in self.solid_lines:
            if line_type == 'h':  # horizontal line
                # Line between (line_r, line_c) and (line_r+1, line_c)
                x0, y0, x1, y1 = self.cell_rect(line_r, line_c)
                x2, y2, x3, y3 = self.cell_rect(line_r + 1, line_c)
                # Draw thick line at the bottom edge of upper cell
                self.canvas.create_line(x0, y1, x1, y1, fill="#ff0000", width=5)
            elif line_type == 'v':  # vertical line
                # Line between (line_r, line_c) and (line_r, line_c+1)
                x0, y0, x1, y1 = self.cell_rect(line_r, line_c)
                x2, y2, x3, y3 = self.cell_rect(line_r, line_c + 1)
                # Draw thick line at the right edge of left cell
                self.canvas.create_line(x1, y0, x1, y1, fill="#ff0000", width=5)

        # Path lines
        if len(self.path) >= 2:
            for (r1, c1), (r2, c2) in zip(self.path, self.path[1:]):
                x1 = GAP + c1 * (CELL + GAP) + CELL // 2
                y1 = GAP + r1 * (CELL + GAP) + CELL // 2
                x2 = GAP + c2 * (CELL + GAP) + CELL // 2
                y2 = GAP + r2 * (CELL + GAP) + CELL // 2
                self.canvas.create_line(x1, y1, x2, y2, fill=path_color, width=10, capstyle=tk.ROUND)

        # Path dots
        for i, (r, c) in enumerate(self.path):
            x0, y0, x1, y1 = self.cell_rect(r, c)
            self.canvas.create_oval(
                x0 + 10, y0 + 10, x1 - 10, y1 - 10,
                outline=path_color, width=3
            )
            if i == len(self.path) - 1:
                # cursor
                self.canvas.create_oval(
                    x0 + 18, y0 + 18, x1 - 18, y1 - 18,
                    outline=cursor_color, width=3
                )

        # Fixed numbers
        for (r, c), num in self.fixed.items():
            x0, y0, x1, y1 = self.cell_rect(r, c)
            self.canvas.create_rectangle(x0+1, y0+1, x1-1, y1-1, fill=num_bg, outline=num_bg)
            self.canvas.create_text(
                (x0+x1)//2, (y0+y1)//2,
                text=str(num), fill=num_fg, font=("Inter", 16, "bold")
            )

        # Optional: show next required number
        if is_victory:
            self.status.config(text="🎉 Puzzle Solved! 🎉")
        elif self.max_fixed > 0 and self.next_required_num <= self.max_fixed:
            self.status.config(text=f"Next required number: {self.next_required_num}")
        elif len(self.path) < self.R * self.C:
            remaining = self.R * self.C - len(self.path)
            self.status.config(text=f"Cells left: {remaining}")
        else:
            self.status.config(text="")

    # ---- Helpers ----
    def in_bounds(self, r, c):
        return 0 <= r < self.R and 0 <= c < self.C

    def is_adjacent(self, a, b):
        (r1, c1), (r2, c2) = a, b
        return abs(r1 - r2) + abs(c1 - c2) == 1

    def cell_from_xy(self, event):
        x, y = event.x, event.y
        # map to grid
        for r in range(self.R):
            for c in range(self.C):
                x0, y0, x1, y1 = self.cell_rect(r, c)
                if x0 <= x <= x1 and y0 <= y <= y1:
                    return (r, c)
        return None

    def can_extend_to(self, r, c):
        # Must be adjacent to last path cell (unless first move)
        if not self.path:
            # If 1 exists, must start on 1.
            if 1 in self.fixed.values():
                return self.fixed.get((r, c)) == 1
            return True  # no 1 clue: any start allowed
        if (r, c) in self.path_set:
            return False
        if not self.is_adjacent(self.path[-1], (r, c)):
            return False
        # Check if this move would cross a solid line
        if crosses_solid_line(self.path[-1], (r, c), self.solid_lines):
            return False
        # If this cell has a number, it must match next_required_num
        here_num = self.fixed.get((r, c))
        if here_num is not None:
            if here_num != self.next_required_num:
                return False
        return True

    def push(self, r, c):
        self.path.append((r, c))
        self.path_set.add((r, c))
        # Update required number if we stepped on a numbered clue
        if (r, c) in self.fixed:
            n = self.fixed[(r, c)]
            if n == self.next_required_num:
                self.next_required_num += 1

    def pop(self):
        if not self.path:
            return
        r, c = self.path.pop()
        self.path_set.remove((r, c))
        # Recompute next_required_num (simpler than tracking a stack of hits)
        self.next_required_num = 1
        for (rr, cc) in self.path:
            if (rr, cc) in self.fixed and self.fixed[(rr, cc)] == self.next_required_num:
                self.next_required_num += 1

    def check_victory(self):
        if len(self.path) != self.R * self.C:
            return False
        # If there are numbered clues, ensure we visited all in order (we enforced while drawing).
        # Final check: contiguous path already enforced; all cells unique already enforced.
        return True

    # ---- Events ----
    def on_click(self, event):
        cell = self.cell_from_xy(event)
        if not cell:
            return
        r, c = cell
        
        # Check if clicking on an already visited node
        if (r, c) in self.path_set:
            # Find the index of this cell in the path
            try:
                target_index = self.path.index((r, c))
                # Reset path to include only up to this node
                self.path = self.path[:target_index + 1]
                self.path_set = set(self.path)
                # Recompute next_required_num
                self.next_required_num = 1
                for (rr, cc) in self.path:
                    if (rr, cc) in self.fixed and self.fixed[(rr, cc)] == self.next_required_num:
                        self.next_required_num += 1
                self.redraw()
                return
            except ValueError:
                pass  # Should not happen since we checked path_set
        
        if not self.path:
            if not self.can_extend_to(r, c):
                self.flash_error("Start on the '1' clue." if 1 in self.fixed.values() else "Invalid start.")
                return
            self.push(r, c)
        else:
            # Clicking can also "step" one
            if self.can_extend_to(r, c):
                self.push(r, c)
                if self.check_victory():
                    self.on_win()
            else:
                self.flash_error("Invalid move.")
        self.dragging = True
        self.redraw()

    def on_drag(self, event):
        if not self.dragging:
            return
        cell = self.cell_from_xy(event)
        if not cell:
            return
        r, c = cell
        if self.path and (r, c) == self.path[-1]:
            return
        if self.can_extend_to(r, c):
            self.push(r, c)
            self.redraw()
            if self.check_victory():
                self.on_win()

    def on_release(self, _event):
        self.dragging = False

    def on_win(self):
        # First redraw to show the green victory state
        self.redraw()
        # Delay the success message to let user see the green path
        self.after(1000, self.show_victory_message)
    
    def show_victory_message(self):
        # Save the completed puzzle to history
        current_puzzle = {
            "name": PUZZLES[self.level_idx]["name"],
            "grid": [row[:] for row in self.grid_data],  # Deep copy
            "solid_lines": self.solid_lines[:],  # Copy solid lines
            "solution_path": self.path[:],  # Copy the solution path
            "timestamp": self.get_timestamp()
        }
        self.completed_puzzles.append(current_puzzle)
        
        messagebox.showinfo("Zip", "You covered every cell with a single path. Nice!")
        
        # Generate a new puzzle instead of advancing to next level
        new_puzzle = generate_new_puzzle()
        PUZZLES.append(new_puzzle)
        self.load_level(len(PUZZLES) - 1)

    def flash_error(self, msg):
        self.status.config(text=msg)
        self.after(1000, lambda: self.status.config(text=""))

if __name__ == "__main__":
    ZipGame().mainloop()
