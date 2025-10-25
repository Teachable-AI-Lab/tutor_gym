# tango.py
# LinkedIn Tango puzzle game clone in Python (Tkinter)
# Run: python tango.py

import tkinter as tk
from tkinter import messagebox
import random
import numpy as np
import datetime

# Game constants
CELL_SIZE = 60
GAP = 2
PADDING = 20
BG_COLOR = "#1a1a1a"
GRID_BG = "#2d2d2d"
CELL_BG = "#3a3a3a"
SUN_COLOR = "#ff8c00"  # Orange sun
MOON_COLOR = "#4a90e2"  # Blue moon
EQUAL_COLOR = "#ffd93d"
DIFF_COLOR = "#ff8c42"
TEXT_COLOR = "#ffffff"
BORDER_COLOR = "#555555"

class TangoGame:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Tango - LinkedIn Puzzle Game")
        self.root.configure(bg=BG_COLOR)
        self.root.resizable(False, False)
        
        # Game state
        self.grid_size = 6
        self.grid = [[None for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        self.constraints = []  # List of constraint tuples (r1, c1, r2, c2, type)
        self.solution = None
        self.completed_puzzles = []  # Store completed puzzles for history
        self.hint_positions = set()  # Track which cells are hints (cannot be changed)
        
        self.setup_ui()
        self.generate_puzzle()
        
    def setup_ui(self):
        """Setup the user interface"""
        # Title
        self.title_label = tk.Label(
            self.root, 
            text="Tango Puzzle", 
            fg=TEXT_COLOR, 
            bg=BG_COLOR, 
            font=("Arial", 20, "bold")
        )
        self.title_label.pack(pady=10)
        
        # Instructions
        self.instructions = tk.Label(
            self.root,
            text="Fill the grid with sun ☀ and moon ☽. Rules: Equal symbols on =, different on ×, max 2 adjacent, equal count per row/column",
            fg=TEXT_COLOR,
            bg=BG_COLOR,
            font=("Arial", 10),
            wraplength=600
        )
        self.instructions.pack(pady=5)
        
        # Canvas for the grid
        canvas_size = self.grid_size * (CELL_SIZE + GAP) + GAP
        self.canvas = tk.Canvas(
            self.root, 
            width=canvas_size, 
            height=canvas_size, 
            bg=GRID_BG, 
            highlightthickness=0
        )
        self.canvas.pack(pady=10)
        
        # Bind click events
        self.canvas.bind("<Button-1>", self.on_cell_click)
        
        # Control buttons
        self.button_frame = tk.Frame(self.root, bg=BG_COLOR)
        self.button_frame.pack(pady=10)
        
        self.new_game_btn = tk.Button(
            self.button_frame,
            text="New Game",
            command=self.new_game,
            bg="#4a4a4a",
            fg="black",
            font=("Arial", 12, "bold"),
            padx=20,
            pady=5
        )
        self.new_game_btn.pack(side=tk.LEFT, padx=5)
        
        self.check_btn = tk.Button(
            self.button_frame,
            text="Check Solution",
            command=self.check_solution,
            bg="#4a4a4a",
            fg="black",
            font=("Arial", 12, "bold"),
            padx=20,
            pady=5
        )
        self.check_btn.pack(side=tk.LEFT, padx=5)
        
        self.hint_btn = tk.Button(
            self.button_frame,
            text="Get Hint",
            command=self.get_hint,
            bg="#4a4a4a",
            fg="black",
            font=("Arial", 12, "bold"),
            padx=20,
            pady=5
        )
        self.hint_btn.pack(side=tk.LEFT, padx=5)
        
        self.solve_btn = tk.Button(
            self.button_frame,
            text="Show Solution",
            command=self.show_solution,
            bg="#4a4a4a",
            fg="black",
            font=("Arial", 12, "bold"),
            padx=20,
            pady=5
        )
        self.solve_btn.pack(side=tk.LEFT, padx=5)
        
        self.history_btn = tk.Button(
            self.button_frame,
            text="History",
            command=self.show_history,
            bg="#4a4a4a",
            fg="black",
            font=("Arial", 12, "bold"),
            padx=20,
            pady=5
        )
        self.history_btn.pack(side=tk.LEFT, padx=5)
        
        # Status label
        self.status_label = tk.Label(
            self.root,
            text="Click cells to place sun ☀ or moon ☽",
            fg=TEXT_COLOR,
            bg=BG_COLOR,
            font=("Arial", 12)
        )
        self.status_label.pack(pady=5)
        
    def generate_puzzle(self):
        """Generate a new Tango puzzle"""
        # Clear the grid
        self.grid = [[None for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        self.constraints = []
        
        # Generate a valid solution first
        self.solution = self.generate_valid_solution()
        
        # Add some constraints (equal and different symbols)
        self.add_constraints()
        
        # Clear some cells to create the puzzle
        self.create_puzzle()
        
        self.draw_grid()
        
    def generate_valid_solution(self):
        """Generate a valid solution for the Tango puzzle with more variety"""
        solution = [[None for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        
        # Start with a more complex pattern instead of simple alternating
        # Create a pattern that's more challenging but still valid
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                # Create a more complex pattern based on position
                if (r * 2 + c) % 3 == 0:
                    solution[r][c] = '☀'  # Sun
                elif (r + c * 2) % 3 == 1:
                    solution[r][c] = '☽'  # Moon
                else:
                    # Fill remaining cells to maintain equal counts
                    if (r + c) % 2 == 0:
                        solution[r][c] = '☀'
                    else:
                        solution[r][c] = '☽'
        
        # Ensure equal counts per row and column
        self.balance_counts(solution)
        
        # Apply more sophisticated transformations to create variety
        for _ in range(50):  # More iterations for better variety
            if not self.apply_smart_transformation(solution):
                break
        
        # Validate the final solution
        if not self.validate_solution(solution):
            # If invalid, regenerate with a simpler approach
            return self.generate_simple_valid_solution()
        
        return solution
    
    def validate_solution(self, solution):
        """Validate that a solution follows all Tango rules"""
        # Check equal counts per row
        for r in range(self.grid_size):
            sun_count = sum(1 for c in range(self.grid_size) if solution[r][c] == '☀')
            moon_count = sum(1 for c in range(self.grid_size) if solution[r][c] == '☽')
            if sun_count != moon_count:
                return False
        
        # Check equal counts per column
        for c in range(self.grid_size):
            sun_count = sum(1 for r in range(self.grid_size) if solution[r][c] == '☀')
            moon_count = sum(1 for r in range(self.grid_size) if solution[r][c] == '☽')
            if sun_count != moon_count:
                return False
        
        # Check adjacency rule (max 2 adjacent)
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if solution[r][c] is not None:
                    # Check horizontal adjacency
                    count = 1
                    # Check left
                    for i in range(1, 3):
                        if c - i >= 0 and solution[r][c-i] == solution[r][c]:
                            count += 1
                        else:
                            break
                    # Check right
                    for i in range(1, 3):
                        if c + i < self.grid_size and solution[r][c+i] == solution[r][c]:
                            count += 1
                        else:
                            break
                    
                    if count > 2:
                        return False
                    
                    # Check vertical adjacency
                    count = 1
                    # Check up
                    for i in range(1, 3):
                        if r - i >= 0 and solution[r-i][c] == solution[r][c]:
                            count += 1
                        else:
                            break
                    # Check down
                    for i in range(1, 3):
                        if r + i < self.grid_size and solution[r+i][c] == solution[r][c]:
                            count += 1
                        else:
                            break
                    
                    if count > 2:
                        return False
        
        return True
    
    def generate_simple_valid_solution(self):
        """Generate a simple but valid solution as fallback"""
        solution = [[None for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        
        # Use a simple alternating pattern that's guaranteed to work
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if (r + c) % 2 == 0:
                    solution[r][c] = '☀'  # Sun
                else:
                    solution[r][c] = '☽'  # Moon
        
        return solution
    
    def balance_counts(self, grid):
        """Ensure equal sun and moon counts per row and column"""
        # Balance rows
        for r in range(self.grid_size):
            sun_count = sum(1 for c in range(self.grid_size) if grid[r][c] == '☀')
            moon_count = sum(1 for c in range(self.grid_size) if grid[r][c] == '☽')
            
            if sun_count > moon_count:
                # Convert some suns to moons
                sun_positions = [(r, c) for c in range(self.grid_size) if grid[r][c] == '☀']
                random.shuffle(sun_positions)
                for i in range((sun_count - moon_count) // 2):
                    if i < len(sun_positions):
                        r_pos, c_pos = sun_positions[i]
                        grid[r_pos][c_pos] = '☽'
            elif moon_count > sun_count:
                # Convert some moons to suns
                moon_positions = [(r, c) for c in range(self.grid_size) if grid[r][c] == '☽']
                random.shuffle(moon_positions)
                for i in range((moon_count - sun_count) // 2):
                    if i < len(moon_positions):
                        r_pos, c_pos = moon_positions[i]
                        grid[r_pos][c_pos] = '☀'
        
        # Balance columns
        for c in range(self.grid_size):
            sun_count = sum(1 for r in range(self.grid_size) if grid[r][c] == '☀')
            moon_count = sum(1 for r in range(self.grid_size) if grid[r][c] == '☽')
            
            if sun_count > moon_count:
                # Convert some suns to moons
                sun_positions = [(r, c) for r in range(self.grid_size) if grid[r][c] == '☀']
                random.shuffle(sun_positions)
                for i in range((sun_count - moon_count) // 2):
                    if i < len(sun_positions):
                        r_pos, c_pos = sun_positions[i]
                        grid[r_pos][c_pos] = '☽'
            elif moon_count > sun_count:
                # Convert some moons to suns
                moon_positions = [(r, c) for r in range(self.grid_size) if grid[r][c] == '☽']
                random.shuffle(moon_positions)
                for i in range((moon_count - sun_count) // 2):
                    if i < len(moon_positions):
                        r_pos, c_pos = moon_positions[i]
                        grid[r_pos][c_pos] = '☀'
    
    def apply_smart_transformation(self, grid):
        """Apply smart transformations to create more challenging patterns"""
        # Try different types of transformations
        transformations = [
            self.swap_adjacent_cells,
            self.swap_diagonal_cells,
            self.swap_opposite_cells,
            self.swap_random_cells
        ]
        
        for transform in transformations:
            if transform(grid):
                return True
        return False
    
    def swap_adjacent_cells(self, grid):
        """Swap adjacent cells if it maintains constraints"""
        for _ in range(10):
            r = random.randint(0, self.grid_size - 1)
            c = random.randint(0, self.grid_size - 1)
            
            # Try adjacent cells
            directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
            random.shuffle(directions)
            
            for dr, dc in directions:
                r2, c2 = r + dr, c + dc
                if 0 <= r2 < self.grid_size and 0 <= c2 < self.grid_size:
                    if self.is_valid_swap(grid, r, c, r2, c2):
                        grid[r][c], grid[r2][c2] = grid[r2][c2], grid[r][c]
                        return True
        return False
    
    def swap_diagonal_cells(self, grid):
        """Swap diagonal cells if it maintains constraints"""
        for _ in range(5):
            r1, c1 = random.randint(0, self.grid_size - 1), random.randint(0, self.grid_size - 1)
            r2, c2 = r1 + random.choice([-1, 1]), c1 + random.choice([-1, 1])
            
            if 0 <= r2 < self.grid_size and 0 <= c2 < self.grid_size:
                if self.is_valid_swap(grid, r1, c1, r2, c2):
                    grid[r1][c1], grid[r2][c2] = grid[r2][c2], grid[r1][c1]
                    return True
        return False
    
    def swap_opposite_cells(self, grid):
        """Swap cells in opposite positions"""
        for _ in range(3):
            r1, c1 = random.randint(0, self.grid_size - 1), random.randint(0, self.grid_size - 1)
            r2, c2 = self.grid_size - 1 - r1, self.grid_size - 1 - c1
            
            if self.is_valid_swap(grid, r1, c1, r2, c2):
                grid[r1][c1], grid[r2][c2] = grid[r2][c2], grid[r1][c1]
                return True
        return False
    
    def swap_random_cells(self, grid):
        """Swap random cells if it maintains constraints"""
        for _ in range(5):
            r1, c1 = random.randint(0, self.grid_size - 1), random.randint(0, self.grid_size - 1)
            r2, c2 = random.randint(0, self.grid_size - 1), random.randint(0, self.grid_size - 1)
            
            if self.is_valid_swap(grid, r1, c1, r2, c2):
                grid[r1][c1], grid[r2][c2] = grid[r2][c2], grid[r1][c1]
                return True
        return False
        
    def is_valid_swap(self, grid, r1, c1, r2, c2):
        """Check if swapping two cells maintains valid constraints"""
        # Create a copy and perform the swap
        temp_grid = [row[:] for row in grid]
        temp_grid[r1][c1], temp_grid[r2][c2] = temp_grid[r2][c2], temp_grid[r1][c1]
        
        # Check if it maintains equal counts per row and column
        for r in range(self.grid_size):
            sun_count = sum(1 for c in range(self.grid_size) if temp_grid[r][c] == '☀')
            moon_count = sum(1 for c in range(self.grid_size) if temp_grid[r][c] == '☽')
            if sun_count != moon_count:
                return False
                
        for c in range(self.grid_size):
            sun_count = sum(1 for r in range(self.grid_size) if temp_grid[r][c] == '☀')
            moon_count = sum(1 for r in range(self.grid_size) if temp_grid[r][c] == '☽')
            if sun_count != moon_count:
                return False
        
        # Check adjacency rule for both swapped positions
        for r, c in [(r1, c1), (r2, c2)]:
            if temp_grid[r][c] is not None:
                # Check horizontal adjacency
                count = 1
                # Check left
                for i in range(1, 3):
                    if c - i >= 0 and temp_grid[r][c-i] == temp_grid[r][c]:
                        count += 1
                    else:
                        break
                # Check right
                for i in range(1, 3):
                    if c + i < self.grid_size and temp_grid[r][c+i] == temp_grid[r][c]:
                        count += 1
                    else:
                        break
                
                if count > 2:
                    return False
                
                # Check vertical adjacency
                count = 1
                # Check up
                for i in range(1, 3):
                    if r - i >= 0 and temp_grid[r-i][c] == temp_grid[r][c]:
                        count += 1
                    else:
                        break
                # Check down
                for i in range(1, 3):
                    if r + i < self.grid_size and temp_grid[r+i][c] == temp_grid[r][c]:
                        count += 1
                    else:
                        break
                
                if count > 2:
                    return False
                
        return True
        
    def add_constraints(self):
        """Add equal and different symbol constraints based on the actual solution"""
        # Add some equal constraints (=) - only between cells with same symbols
        equal_candidates = []
        for r1 in range(self.grid_size):
            for c1 in range(self.grid_size):
                for dr, dc in [(0, 1), (1, 0)]:  # Only check right and down to avoid duplicates
                    r2, c2 = r1 + dr, c1 + dc
                    if 0 <= r2 < self.grid_size and 0 <= c2 < self.grid_size:
                        # Only add = constraint if symbols are actually the same
                        if self.solution[r1][c1] == self.solution[r2][c2]:
                            equal_candidates.append((r1, c1, r2, c2))
        
        # Randomly select some equal constraints
        random.shuffle(equal_candidates)
        equal_count = min(4, len(equal_candidates))
        for i in range(equal_count):
            r1, c1, r2, c2 = equal_candidates[i]
            self.constraints.append((r1, c1, r2, c2, '='))
        
        # Add some different constraints (×) - only between cells with different symbols
        different_candidates = []
        for r1 in range(self.grid_size):
            for c1 in range(self.grid_size):
                for dr, dc in [(0, 1), (1, 0)]:  # Only check right and down to avoid duplicates
                    r2, c2 = r1 + dr, c1 + dc
                    if 0 <= r2 < self.grid_size and 0 <= c2 < self.grid_size:
                        # Only add × constraint if symbols are actually different
                        if self.solution[r1][c1] != self.solution[r2][c2]:
                            different_candidates.append((r1, c1, r2, c2))
        
        # Randomly select some different constraints
        random.shuffle(different_candidates)
        different_count = min(3, len(different_candidates))
        for i in range(different_count):
            r1, c1, r2, c2 = different_candidates[i]
            self.constraints.append((r1, c1, r2, c2, '×'))
                        
    def create_puzzle(self):
        """Create the puzzle by providing strategic hints"""
        # Start with all cells empty
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                self.grid[r][c] = None
        
        # Determine number of hints (4-14, skewed towards lower bound)
        # Use weighted random to favor lower numbers
        weights = [0.3, 0.25, 0.2, 0.15, 0.1]  # Higher weights for lower numbers
        hint_ranges = [(4, 6), (7, 8), (9, 10), (11, 12), (13, 14)]
        selected_range = random.choices(hint_ranges, weights=weights)[0]
        hint_count = random.randint(selected_range[0], selected_range[1])
        
        # Get strategic hint positions
        hint_positions = self.get_strategic_hints(hint_count)
        
        # Place hints from the solution and mark them as unchangeable
        self.hint_positions = set(hint_positions)
        for r, c in hint_positions:
            self.grid[r][c] = self.solution[r][c]
        
        # Verify no constraint has both sides filled
        self.validate_constraint_hints()
        
        # Verify the puzzle is solvable with these hints
        if not self.verify_puzzle_solvability():
            # If not solvable, add more hints
            self.add_additional_hints()
    
    def get_strategic_hints(self, hint_count):
        """Get strategic positions for hints to ensure solvability"""
        hint_positions = []
        
        # Priority 1: Constraint-related positions (but only some constraints, not all)
        constraint_positions = set()
        used_constraints = set()  # Track which constraints we've already used
        
        for r1, c1, r2, c2, _ in self.constraints:
            # Only fill hints for about 15-25% of constraints (much fewer)
            if random.random() < 0.2:  # 20% chance to include this constraint
                # Make sure we haven't already used this constraint
                constraint_key = tuple(sorted([(r1, c1), (r2, c2)]))
                if constraint_key not in used_constraints:
                    used_constraints.add(constraint_key)
                    # Randomly choose one side of this constraint
                    if random.choice([True, False]):
                        constraint_positions.add((r1, c1))
                    else:
                        constraint_positions.add((r2, c2))
        
        # Add constraint positions first
        for pos in constraint_positions:
            if len(hint_positions) < hint_count:
                hint_positions.append(pos)
        
        # Priority 2: Corner positions (help with adjacency rules)
        corners = [(0, 0), (0, self.grid_size-1), (self.grid_size-1, 0), (self.grid_size-1, self.grid_size-1)]
        for corner in corners:
            if corner not in hint_positions and len(hint_positions) < hint_count:
                hint_positions.append(corner)
        
        # Priority 3: Edge positions
        edge_positions = []
        for r in range(self.grid_size):
            edge_positions.extend([(r, 0), (r, self.grid_size-1)])
        for c in range(self.grid_size):
            edge_positions.extend([(0, c), (self.grid_size-1, c)])
        
        # Remove duplicates and already selected positions
        edge_positions = list(set(edge_positions) - set(hint_positions))
        random.shuffle(edge_positions)
        
        for pos in edge_positions:
            if len(hint_positions) < hint_count:
                hint_positions.append(pos)
        
        # Priority 4: Center positions
        center_positions = []
        for r in range(1, self.grid_size-1):
            for c in range(1, self.grid_size-1):
                center_positions.append((r, c))
        
        # Remove already selected positions
        center_positions = list(set(center_positions) - set(hint_positions))
        random.shuffle(center_positions)
        
        for pos in center_positions:
            if len(hint_positions) < hint_count:
                hint_positions.append(pos)
        
        return hint_positions
    
    def verify_puzzle_solvability(self):
        """Verify that the current puzzle can be solved by deduction"""
        # Try to solve the puzzle using logical deduction
        temp_grid = [row[:] for row in self.grid]
        
        # Apply constraint-based deduction
        changed = True
        while changed:
            changed = False
            
            # Apply constraint rules
            for r1, c1, r2, c2, constraint_type in self.constraints:
                if temp_grid[r1][c1] is not None and temp_grid[r2][c2] is None:
                    if constraint_type == '=':
                        temp_grid[r2][c2] = temp_grid[r1][c1]
                        changed = True
                    elif constraint_type == '×':
                        temp_grid[r2][c2] = '☽' if temp_grid[r1][c1] == '☀' else '☀'
                        changed = True
                elif temp_grid[r1][c1] is None and temp_grid[r2][c2] is not None:
                    if constraint_type == '=':
                        temp_grid[r1][c1] = temp_grid[r2][c2]
                        changed = True
                    elif constraint_type == '×':
                        temp_grid[r1][c1] = '☽' if temp_grid[r2][c2] == '☀' else '☀'
                        changed = True
            
            # Apply adjacency rules
            for r in range(self.grid_size):
                for c in range(self.grid_size):
                    if temp_grid[r][c] is None:
                        # Check if we can deduce this cell based on adjacency
                        symbol = self.deduce_from_adjacency(temp_grid, r, c)
                        if symbol is not None:
                            temp_grid[r][c] = symbol
                            changed = True
            
            # Apply row/column balance rules
            for r in range(self.grid_size):
                if self.apply_row_balance_rule(temp_grid, r):
                    changed = True
            
            for c in range(self.grid_size):
                if self.apply_column_balance_rule(temp_grid, c):
                    changed = True
        
        # Check if puzzle is fully solved
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if temp_grid[r][c] is None:
                    return False
        
        return True
    
    def deduce_from_adjacency(self, grid, r, c):
        """Deduce cell value based on adjacency rules"""
        # Check horizontal adjacency
        left_symbols = []
        right_symbols = []
        
        # Check left
        for i in range(1, 3):
            if c - i >= 0 and grid[r][c-i] is not None:
                left_symbols.append(grid[r][c-i])
            else:
                break
        
        # Check right
        for i in range(1, 3):
            if c + i < self.grid_size and grid[r][c+i] is not None:
                right_symbols.append(grid[r][c+i])
            else:
                break
        
        # If we have 2 identical symbols on one side, this cell must be different
        if len(left_symbols) == 2 and left_symbols[0] == left_symbols[1]:
            return '☽' if left_symbols[0] == '☀' else '☀'
        if len(right_symbols) == 2 and right_symbols[0] == right_symbols[1]:
            return '☽' if right_symbols[0] == '☀' else '☀'
        
        # Check vertical adjacency
        up_symbols = []
        down_symbols = []
        
        # Check up
        for i in range(1, 3):
            if r - i >= 0 and grid[r-i][c] is not None:
                up_symbols.append(grid[r-i][c])
            else:
                break
        
        # Check down
        for i in range(1, 3):
            if r + i < self.grid_size and grid[r+i][c] is not None:
                down_symbols.append(grid[r+i][c])
            else:
                break
        
        # If we have 2 identical symbols on one side, this cell must be different
        if len(up_symbols) == 2 and up_symbols[0] == up_symbols[1]:
            return '☽' if up_symbols[0] == '☀' else '☀'
        if len(down_symbols) == 2 and down_symbols[0] == down_symbols[1]:
            return '☽' if down_symbols[0] == '☀' else '☀'
        
        return None
    
    def apply_row_balance_rule(self, grid, r):
        """Apply row balance rule to deduce missing cells"""
        sun_count = sum(1 for c in range(self.grid_size) if grid[r][c] == '☀')
        moon_count = sum(1 for c in range(self.grid_size) if grid[r][c] == '☽')
        empty_count = sum(1 for c in range(self.grid_size) if grid[r][c] is None)
        
        if empty_count == 0:
            return False
        
        # If we need more suns
        if sun_count < self.grid_size // 2 and empty_count == (self.grid_size // 2 - sun_count):
            for c in range(self.grid_size):
                if grid[r][c] is None:
                    grid[r][c] = '☀'
            return True
        
        # If we need more moons
        if moon_count < self.grid_size // 2 and empty_count == (self.grid_size // 2 - moon_count):
            for c in range(self.grid_size):
                if grid[r][c] is None:
                    grid[r][c] = '☽'
            return True
        
        return False
    
    def apply_column_balance_rule(self, grid, c):
        """Apply column balance rule to deduce missing cells"""
        sun_count = sum(1 for r in range(self.grid_size) if grid[r][c] == '☀')
        moon_count = sum(1 for r in range(self.grid_size) if grid[r][c] == '☽')
        empty_count = sum(1 for r in range(self.grid_size) if grid[r][c] is None)
        
        if empty_count == 0:
            return False
        
        # If we need more suns
        if sun_count < self.grid_size // 2 and empty_count == (self.grid_size // 2 - sun_count):
            for r in range(self.grid_size):
                if grid[r][c] is None:
                    grid[r][c] = '☀'
            return True
        
        # If we need more moons
        if moon_count < self.grid_size // 2 and empty_count == (self.grid_size // 2 - moon_count):
            for r in range(self.grid_size):
                if grid[r][c] is None:
                    grid[r][c] = '☽'
            return True
        
        return False
    
    def add_additional_hints(self):
        """Add additional hints if puzzle is not solvable"""
        # Find empty cells and add more hints
        empty_cells = []
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if self.grid[r][c] is None:
                    empty_cells.append((r, c))
        
        # Add up to 3 more hints
        additional_hints = min(3, len(empty_cells))
        random.shuffle(empty_cells)
        
        for i in range(additional_hints):
            r, c = empty_cells[i]
            self.grid[r][c] = self.solution[r][c]
            self.hint_positions.add((r, c))  # Mark as hint position
    
    def validate_constraint_hints(self):
        """Ensure no constraint has both sides filled"""
        for r1, c1, r2, c2, _ in self.constraints:
            if self.grid[r1][c1] is not None and self.grid[r2][c2] is not None:
                # Both sides are filled - remove one side randomly
                if random.choice([True, False]):
                    self.grid[r1][c1] = None
                    self.hint_positions.discard((r1, c1))
                else:
                    self.grid[r2][c2] = None
                    self.hint_positions.discard((r2, c2))
            
    def draw_grid(self):
        """Draw the game grid"""
        self.canvas.delete("all")
        
        # Draw cells
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                x1 = c * (CELL_SIZE + GAP) + GAP
                y1 = r * (CELL_SIZE + GAP) + GAP
                x2 = x1 + CELL_SIZE
                y2 = y1 + CELL_SIZE
                
                # Draw cell background
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=CELL_BG, outline=BORDER_COLOR, width=1)
                
                # Draw symbol if present
                if self.grid[r][c] is not None:
                    center_x = (x1 + x2) // 2
                    center_y = (y1 + y2) // 2
                    
                    if self.grid[r][c] == '☀':
                        self.canvas.create_text(center_x, center_y, text='☀', fill=SUN_COLOR, font=("Arial", 24, "bold"))
                    else:
                        self.canvas.create_text(center_x, center_y, text='☽', fill=MOON_COLOR, font=("Arial", 24, "bold"))
        
        # Draw constraints
        for r1, c1, r2, c2, constraint_type in self.constraints:
            x1 = c1 * (CELL_SIZE + GAP) + GAP + CELL_SIZE
            y1 = r1 * (CELL_SIZE + GAP) + GAP + CELL_SIZE // 2
            x2 = c2 * (CELL_SIZE + GAP) + GAP
            y2 = r2 * (CELL_SIZE + GAP) + GAP + CELL_SIZE // 2
            
            # Determine constraint position
            if c2 > c1:  # Horizontal constraint
                x1 = c1 * (CELL_SIZE + GAP) + GAP + CELL_SIZE
                y1 = r1 * (CELL_SIZE + GAP) + GAP + CELL_SIZE // 2
                x2 = c2 * (CELL_SIZE + GAP) + GAP
                y2 = y1
            elif c2 < c1:  # Horizontal constraint
                x1 = c1 * (CELL_SIZE + GAP) + GAP
                y1 = r1 * (CELL_SIZE + GAP) + GAP + CELL_SIZE // 2
                x2 = c2 * (CELL_SIZE + GAP) + GAP + CELL_SIZE
                y2 = y1
            elif r2 > r1:  # Vertical constraint
                x1 = c1 * (CELL_SIZE + GAP) + GAP + CELL_SIZE // 2
                y1 = r1 * (CELL_SIZE + GAP) + GAP + CELL_SIZE
                x2 = x1
                y2 = r2 * (CELL_SIZE + GAP) + GAP
            else:  # Vertical constraint
                x1 = c1 * (CELL_SIZE + GAP) + GAP + CELL_SIZE // 2
                y1 = r1 * (CELL_SIZE + GAP) + GAP
                x2 = x1
                y2 = r2 * (CELL_SIZE + GAP) + GAP + CELL_SIZE
            
            # Draw constraint symbol
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            
            if constraint_type == '=':
                self.canvas.create_text(center_x, center_y, text='=', fill=EQUAL_COLOR, font=("Arial", 16, "bold"))
            else:
                self.canvas.create_text(center_x, center_y, text='×', fill=DIFF_COLOR, font=("Arial", 16, "bold"))
                
    def on_cell_click(self, event):
        """Handle cell click events"""
        # Calculate which cell was clicked
        c = event.x // (CELL_SIZE + GAP)
        r = event.y // (CELL_SIZE + GAP)
        
        if 0 <= r < self.grid_size and 0 <= c < self.grid_size:
            # Don't allow changing hint positions
            if (r, c) in self.hint_positions:
                self.status_label.config(text="Cannot change hint positions!")
                return
            
            # Cycle through: None -> Sun -> Moon -> None
            if self.grid[r][c] is None:
                self.grid[r][c] = '☀'  # Sun
            elif self.grid[r][c] == '☀':
                self.grid[r][c] = '☽'  # Moon
            else:
                self.grid[r][c] = None
                
            self.draw_grid()
            
    def check_solution(self):
        """Check if the current solution is correct"""
        # Check if all cells are filled
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if self.grid[r][c] is None:
                    self.status_label.config(text="Please fill all cells")
                    return
        
        # Check equal counts per row
        for r in range(self.grid_size):
            sun_count = sum(1 for c in range(self.grid_size) if self.grid[r][c] == '☀')
            moon_count = sum(1 for c in range(self.grid_size) if self.grid[r][c] == '☽')
            if sun_count != moon_count:
                self.status_label.config(text=f"Row {r+1} doesn't have equal sun and moon counts")
                return
        
        # Check equal counts per column
        for c in range(self.grid_size):
            sun_count = sum(1 for r in range(self.grid_size) if self.grid[r][c] == '☀')
            moon_count = sum(1 for r in range(self.grid_size) if self.grid[r][c] == '☽')
            if sun_count != moon_count:
                self.status_label.config(text=f"Column {c+1} doesn't have equal sun and moon counts")
                return
        
        # Check adjacent constraint (max 2 adjacent)
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if self.grid[r][c] is not None:
                    # Check horizontal adjacency
                    count = 1
                    # Check left
                    for i in range(1, 3):
                        if c - i >= 0 and self.grid[r][c-i] == self.grid[r][c]:
                            count += 1
                        else:
                            break
                    # Check right
                    for i in range(1, 3):
                        if c + i < self.grid_size and self.grid[r][c+i] == self.grid[r][c]:
                            count += 1
                        else:
                            break
                    
                    if count > 2:
                        symbol_name = "suns" if self.grid[r][c] == '☀' else "moons"
                        self.status_label.config(text=f"Too many adjacent {symbol_name} in row {r+1}")
                        return
                    
                    # Check vertical adjacency
                    count = 1
                    # Check up
                    for i in range(1, 3):
                        if r - i >= 0 and self.grid[r-i][c] == self.grid[r][c]:
                            count += 1
                        else:
                            break
                    # Check down
                    for i in range(1, 3):
                        if r + i < self.grid_size and self.grid[r+i][c] == self.grid[r][c]:
                            count += 1
                        else:
                            break
                    
                    if count > 2:
                        symbol_name = "suns" if self.grid[r][c] == '☀' else "moons"
                        self.status_label.config(text=f"Too many adjacent {symbol_name} in column {c+1}")
                        return
        
        # Check constraints
        for r1, c1, r2, c2, constraint_type in self.constraints:
            if self.grid[r1][c1] is not None and self.grid[r2][c2] is not None:
                if constraint_type == '=' and self.grid[r1][c1] != self.grid[r2][c2]:
                    self.status_label.config(text=f"Cells connected by = must be equal")
                    return
                elif constraint_type == '×' and self.grid[r1][c1] == self.grid[r2][c2]:
                    self.status_label.config(text=f"Cells connected by × must be different")
                    return
        
        # All checks passed
        self.status_label.config(text="🎉 Congratulations! Solution is correct! 🎉")
        self.root.after(1500, self.show_victory_and_new_game)
    
    def show_victory_and_new_game(self):
        """Show victory message and generate new puzzle"""
        # Save the completed puzzle
        self.save_completed_puzzle()
        
        messagebox.showinfo("Tango", "Congratulations! You solved the puzzle! Generating new puzzle...")
        self.generate_puzzle()
        self.status_label.config(text="New puzzle generated! Click cells to place sun ☀ or moon ☽")
        
    def get_hint(self):
        """Provide a hint by revealing one correct cell"""
        if not self.solution:
            self.status_label.config(text="No solution available")
            return
        
        # Find empty cells
        empty_cells = []
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if self.grid[r][c] is None:
                    empty_cells.append((r, c))
        
        if not empty_cells:
            self.status_label.config(text="All cells are filled!")
            return
        
        # Choose a strategic hint position
        hint_pos = self.choose_strategic_hint(empty_cells)
        
        if hint_pos:
            r, c = hint_pos
            self.grid[r][c] = self.solution[r][c]
            self.hint_positions.add((r, c))  # Mark as hint position
            self.draw_grid()
            self.status_label.config(text=f"Hint revealed at position ({r+1}, {c+1})")
        else:
            # Fallback: reveal a random empty cell
            r, c = random.choice(empty_cells)
            self.grid[r][c] = self.solution[r][c]
            self.hint_positions.add((r, c))  # Mark as hint position
            self.draw_grid()
            self.status_label.config(text=f"Hint revealed at position ({r+1}, {c+1})")
    
    def choose_strategic_hint(self, empty_cells):
        """Choose a strategic position for the hint"""
        # Priority 1: Cells involved in constraints (but only one side)
        constraint_cells = set()
        for r1, c1, r2, c2, _ in self.constraints:
            # Only add if one side is filled and the other is empty
            if (r1, c1) in empty_cells and self.grid[r2][c2] is not None:
                constraint_cells.add((r1, c1))
            elif (r2, c2) in empty_cells and self.grid[r1][c1] is not None:
                constraint_cells.add((r2, c2))
        
        # Filter out constraint cells that would create both sides filled
        safe_constraint_cells = []
        for r, c in constraint_cells:
            # Check if this would be the second side of a constraint
            would_fill_both_sides = False
            for r1, c1, r2, c2, _ in self.constraints:
                if ((r, c) == (r1, c1) and self.grid[r2][c2] is not None) or \
                   ((r, c) == (r2, c2) and self.grid[r1][c1] is not None):
                    would_fill_both_sides = True
                    break
            
            if not would_fill_both_sides:
                safe_constraint_cells.append((r, c))
        
        if safe_constraint_cells:
            return random.choice(safe_constraint_cells)
        
        # Priority 2: Cells that would help with adjacency rules
        adjacency_help_cells = []
        for r, c in empty_cells:
            if self.would_help_adjacency(r, c):
                adjacency_help_cells.append((r, c))
        
        if adjacency_help_cells:
            return random.choice(adjacency_help_cells)
        
        # Priority 3: Cells that would help with row/column balance
        balance_help_cells = []
        for r, c in empty_cells:
            if self.would_help_balance(r, c):
                balance_help_cells.append((r, c))
        
        if balance_help_cells:
            return random.choice(balance_help_cells)
        
        return None
    
    def would_help_adjacency(self, r, c):
        """Check if revealing this cell would help with adjacency rules"""
        # Check if there are adjacent cells that could benefit from this hint
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        for dr, dc in directions:
            r2, c2 = r + dr, c + dc
            if 0 <= r2 < self.grid_size and 0 <= c2 < self.grid_size:
                if self.grid[r2][c2] is not None:
                    # Check if this would help deduce the value
                    symbol = self.solution[r][c]
                    if symbol != self.grid[r2][c2]:
                        return True
        return False
    
    def would_help_balance(self, r, c):
        """Check if revealing this cell would help with row/column balance"""
        # Check row balance
        row_sun_count = sum(1 for c2 in range(self.grid_size) if self.grid[r][c2] == '☀')
        row_moon_count = sum(1 for c2 in range(self.grid_size) if self.grid[r][c2] == '☽')
        row_empty_count = sum(1 for c2 in range(self.grid_size) if self.grid[r][c2] is None)
        
        if row_empty_count == 1:  # This is the last empty cell in the row
            return True
        
        # Check column balance
        col_sun_count = sum(1 for r2 in range(self.grid_size) if self.grid[r2][c] == '☀')
        col_moon_count = sum(1 for r2 in range(self.grid_size) if self.grid[r2][c] == '☽')
        col_empty_count = sum(1 for r2 in range(self.grid_size) if self.grid[r2][c] is None)
        
        if col_empty_count == 1:  # This is the last empty cell in the column
            return True
        
        return False
    
    def show_solution(self):
        """Show the correct solution with cell-by-cell animation"""
        if not self.solution:
            self.status_label.config(text="No solution available")
            return
        
        # Find all empty cells
        empty_cells = []
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if self.grid[r][c] is None:
                    empty_cells.append((r, c))
        
        if not empty_cells:
            self.status_label.config(text="Puzzle already solved!")
            return
        
        # Animate filling cells one by one
        self.animate_solution(empty_cells)
    
    def animate_solution(self, empty_cells):
        """Animate the solution by filling cells one by one"""
        if not empty_cells:
            # Solution complete - show completion message and auto-generate new puzzle
            self.status_label.config(text="🎉 Solution Complete! 🎉")
            self.root.after(1500, self.show_completion_and_new_game)
            return
        
        # Fill the next cell
        r, c = empty_cells[0]
        self.grid[r][c] = self.solution[r][c]
        self.draw_grid()
        
        # Update status
        remaining = len(empty_cells) - 1
        if remaining > 0:
            self.status_label.config(text=f"Filling solution... {remaining} cells remaining")
        else:
            self.status_label.config(text="Solution complete!")
        
        # Continue with next cell after a short delay
        self.root.after(200, lambda: self.animate_solution(empty_cells[1:]))
    
    def show_completion_and_new_game(self):
        """Show completion message and generate new puzzle"""
        # Save the completed puzzle
        self.save_completed_puzzle()
        
        messagebox.showinfo("Tango", "Congratulations! Puzzle solved! Generating new puzzle...")
        self.generate_puzzle()
        self.status_label.config(text="New puzzle generated! Click cells to place sun ☀ or moon ☽")
            
    def save_completed_puzzle(self):
        """Save the current puzzle to completed puzzles history"""
        puzzle_data = {
            'name': f"Tango Puzzle {len(self.completed_puzzles) + 1}",
            'grid': [row[:] for row in self.grid],
            'solution': [row[:] for row in self.solution],
            'constraints': self.constraints[:],
            'hint_positions': self.hint_positions.copy(),
            'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.completed_puzzles.append(puzzle_data)
    
    def show_history(self):
        """Show completed puzzles history"""
        if not self.completed_puzzles:
            messagebox.showinfo("History", "No completed puzzles yet!")
            return
        
        # Create history window
        history_window = tk.Toplevel(self.root)
        history_window.title("Completed Puzzles")
        history_window.configure(bg=BG_COLOR)
        history_window.geometry("600x400")
        
        # Title
        title_label = tk.Label(
            history_window,
            text="Completed Puzzles",
            fg=TEXT_COLOR,
            bg=BG_COLOR,
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=10)
        
        # Create scrollable frame
        canvas = tk.Canvas(history_window, bg=BG_COLOR, highlightthickness=0)
        scrollbar = tk.Scrollbar(history_window, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=BG_COLOR)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Add puzzle entries
        for i, puzzle in enumerate(self.completed_puzzles):
            puzzle_frame = tk.Frame(scrollable_frame, bg=BG_COLOR, relief=tk.RAISED, bd=1)
            puzzle_frame.pack(fill=tk.X, padx=10, pady=5)
            
            # Puzzle info
            info_label = tk.Label(
                puzzle_frame,
                text=f"{puzzle['name']} - {puzzle['timestamp']}",
                fg=TEXT_COLOR,
                bg=BG_COLOR,
                font=("Arial", 12, "bold")
            )
            info_label.pack(pady=5)
            
            # Replay button
            replay_btn = tk.Button(
                puzzle_frame,
                text="Replay",
                command=lambda p=puzzle: self.replay_puzzle(p),
                bg="#4a4a4a",
                fg="black",
                font=("Arial", 10, "bold"),
                padx=15,
                pady=3
            )
            replay_btn.pack(pady=5)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def replay_puzzle(self, puzzle):
        """Replay a completed puzzle"""
        # Load the puzzle data but start with empty grid
        self.solution = [row[:] for row in puzzle['solution']]
        self.constraints = puzzle['constraints'][:]
        
        # Start with completely empty grid
        self.grid = [[None for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        
        # Only place the original hints (not the full solution)
        if 'hint_positions' in puzzle:
            # Use saved hint positions
            self.hint_positions = puzzle['hint_positions'].copy()
            for r, c in self.hint_positions:
                self.grid[r][c] = self.solution[r][c]
        else:
            # Fallback for old saved puzzles - reconstruct original hints
            # Find which cells were originally hints by comparing with solution
            original_hints = []
            for r in range(self.grid_size):
                for c in range(self.grid_size):
                    if puzzle['grid'][r][c] is not None:
                        original_hints.append((r, c))
            
            self.hint_positions = set(original_hints)
            for r, c in original_hints:
                self.grid[r][c] = self.solution[r][c]
        
        # Redraw the grid
        self.draw_grid()
        
        # Update status
        self.status_label.config(text=f"Replaying: {puzzle['name']}")
        
        # Close history window if it exists
        for window in self.root.winfo_children():
            if isinstance(window, tk.Toplevel):
                window.destroy()
    
    def new_game(self):
        """Start a new game"""
        self.generate_puzzle()
        self.status_label.config(text="New game started! Click cells to place sun ☀ or moon ☽")
        
    def run(self):
        """Start the game"""
        self.root.mainloop()

if __name__ == "__main__":
    game = TangoGame()
    game.run()
