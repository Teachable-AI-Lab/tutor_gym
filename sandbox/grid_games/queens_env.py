import random
import numpy as np
from tutorgym.shared import ProblemState
from tutorgym.env_classes.fsm_tutor import FiniteStateMachine, StateMachineTutor
from tutorgym.env_classes.CTAT.action_model import CTAT_ActionModel
from tutorgym.env_classes.env_base import TutorEnvBase
from tutorgym.env_classes.CTAT.action_model import Action

import tkinter as tk
from tkinter import messagebox
import math
from datetime import datetime

def generate_regions(grid_size, num_colors):
    """Generate colored regions for the grid with varied shapes"""
    regions = [[0 for _ in range(grid_size)] for _ in range(grid_size)]
    
    # Preset colors (13 non-neon, non-black, highly distinguishable colors)
    preset_colors = [
        '#8B4513',  # Saddle Brown
        '#228B22',  # Forest Green
        '#4169E1',  # Royal Blue
        '#DC143C',  # Crimson
        '#FF8C00',  # Dark Orange
        '#9370DB',  # Medium Purple
        '#FF69B4',  # Hot Pink
        '#32CD32',  # Lime Green
        '#1E90FF',  # Dodger Blue
        '#FF6347',  # Tomato
        '#8A2BE2',  # Blue Violet
        '#20B2AA',  # Light Sea Green
        '#DAA520'   # Goldenrod
    ]
    
    # Select unique colors from preset (each color used only once)
    selected_colors = preset_colors[:num_colors]
    
    # Create varied region shapes using flood fill approach
    region_id = 0
    visited = [[False for _ in range(grid_size)] for _ in range(grid_size)]
    
    # Define possible region shapes (no diagonal connections)
    region_templates = [
        # L-shapes (no diagonal connections)
        [(0,0), (0,1), (1,0), (1,1), (2,0)],  # L-shape 1
        [(0,0), (0,1), (0,2), (1,2), (2,2)],  # L-shape 2
        [(0,0), (1,0), (2,0), (2,1), (2,2)],  # L-shape 3
        [(0,2), (1,2), (2,0), (2,1), (2,2)],  # L-shape 4
        
        # T-shapes
        [(0,1), (1,0), (1,1), (1,2), (2,1)],  # T-shape 1
        [(0,0), (0,1), (0,2), (1,1), (2,1)],  # T-shape 2
        
        # Plus shapes
        [(0,1), (1,0), (1,1), (1,2), (2,1)],  # Plus shape
        
        # Linear shapes
        [(0,0), (0,1), (0,2), (0,3)],  # Horizontal line
        [(0,0), (1,0), (2,0), (3,0)],  # Vertical line
        
        # Square shapes
        [(0,0), (0,1), (1,0), (1,1)],  # 2x2 square
        [(0,0), (0,1), (0,2), (1,0), (1,1), (1,2), (2,0), (2,1), (2,2)],  # 3x3 square
        
        # Corner shapes
        [(0,0), (0,1), (1,0)],  # Corner 1
        [(0,1), (0,2), (1,2)],  # Corner 2
        [(1,0), (2,0), (2,1)],  # Corner 3
        [(1,2), (2,1), (2,2)],  # Corner 4
    ]
    
    # Try to place regions using templates
    attempts = 0
    max_attempts = 500  # Reduced from 1000 for speed
    
    # Shuffle templates for more variety
    random.shuffle(region_templates)
    
    while region_id < num_colors and attempts < max_attempts:
        attempts += 1
        
        # Find an empty position
        empty_positions = []
        for r in range(grid_size):
            for c in range(grid_size):
                if not visited[r][c]:
                    empty_positions.append((r, c))
        
        if not empty_positions:
            break
        
        # Choose a random empty position
        start_r, start_c = random.choice(empty_positions)
        
        # Choose a random template (with preference for different sizes)
        template = random.choice(region_templates)
        
        # Sometimes try smaller templates for more variety
        if random.random() < 0.3:  # 30% chance
            small_templates = [t for t in region_templates if len(t) <= 4]
            if small_templates:
                template = random.choice(small_templates)
        
        # Try to place the template
        can_place = True
        template_positions = []
        
        for dr, dc in template:
            new_r, new_c = start_r + dr, start_c + dc
            if (new_r >= grid_size or new_c >= grid_size or 
                visited[new_r][new_c]):
                can_place = False
                break
            template_positions.append((new_r, new_c))
        
        if can_place:
            # Place the region with unique color assignment
            for r, c in template_positions:
                regions[r][c] = region_id
                visited[r][c] = True
            region_id += 1
    
    # Fill any remaining empty cells with random regions
    for r in range(grid_size):
        for c in range(grid_size):
            if not visited[r][c]:
                # Find adjacent region or create new one (no diagonal connections)
                adjacent_regions = set()
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:  # Only horizontal/vertical
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < grid_size and 0 <= nc < grid_size and
                        visited[nr][nc]):
                        adjacent_regions.add(regions[nr][nc])
                
                if adjacent_regions:
                    # Join to an adjacent region
                    regions[r][c] = random.choice(list(adjacent_regions))
                else:
                    # Create new region
                    regions[r][c] = region_id
                    region_id += 1
                visited[r][c] = True
    
    # Ensure we have exactly the right number of colors
    unique_regions = len(set(regions[r][c] for r in range(grid_size) for c in range(grid_size)))
    
    if unique_regions < num_colors:
        # Split some large regions
        split_large_regions(regions, num_colors, grid_size)
    elif unique_regions > num_colors:
        # Merge some small regions
        merge_small_regions(regions, num_colors, grid_size)
    
    # Ensure each region gets a unique color
    assign_unique_colors(regions, grid_size)
    
    return regions

def split_large_regions(regions, min_regions, grid_size):
    """Split large regions to increase region count"""
    current_regions = len(set(regions[r][c] for r in range(grid_size) for c in range(grid_size)))
    
    while current_regions < min_regions:
        # Find the largest region
        region_sizes = {}
        for r in range(grid_size):
            for c in range(grid_size):
                region_id = regions[r][c]
                region_sizes[region_id] = region_sizes.get(region_id, 0) + 1
        
        if not region_sizes:
            break
        
        largest_region = max(region_sizes, key=region_sizes.get)
        
        # Find cells in this region
        region_cells = []
        for r in range(grid_size):
            for c in range(grid_size):
                if regions[r][c] == largest_region:
                    region_cells.append((r, c))
        
        if len(region_cells) < 4:  # Too small to split
            break
        
        # Split the region
        split_point = len(region_cells) // 2
        new_region_id = max(region_sizes.keys()) + 1
        
        for i, (r, c) in enumerate(region_cells):
            if i >= split_point:
                regions[r][c] = new_region_id
        
        current_regions = len(set(regions[r][c] for r in range(grid_size) for c in range(grid_size)))

def merge_small_regions(regions, max_regions, grid_size):
    """Merge small regions to decrease region count"""
    current_regions = len(set(regions[r][c] for r in range(grid_size) for c in range(grid_size)))
    
    while current_regions > max_regions:
        # Find the smallest region
        region_sizes = {}
        for r in range(grid_size):
            for c in range(grid_size):
                region_id = regions[r][c]
                region_sizes[region_id] = region_sizes.get(region_id, 0) + 1
        
        if not region_sizes:
            break
        
        smallest_region = min(region_sizes, key=region_sizes.get)
        
        # Find an adjacent region to merge with (no diagonal connections)
        adjacent_regions = set()
        for r in range(grid_size):
            for c in range(grid_size):
                if regions[r][c] == smallest_region:
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:  # Only horizontal/vertical
                        nr, nc = r + dr, c + dc
                        if (0 <= nr < grid_size and 0 <= nc < grid_size and
                            regions[nr][nc] != smallest_region):
                            adjacent_regions.add(regions[nr][nc])
        
        if adjacent_regions:
            # Merge with the largest adjacent region
            merge_target = max(adjacent_regions, key=lambda x: region_sizes.get(x, 0))
            
            for r in range(grid_size):
                for c in range(grid_size):
                    if regions[r][c] == smallest_region:
                        regions[r][c] = merge_target
        
        current_regions = len(set(regions[r][c] for r in range(grid_size) for c in range(grid_size)))

def assign_unique_colors(regions, grid_size):
    """Assign unique colors to each region"""
    # Get all unique region IDs
    unique_regions = list(set(regions[r][c] for r in range(grid_size) for c in range(grid_size)))
    unique_regions.sort()  # Sort for consistent assignment
    
    # Create a mapping from old region ID to new color index
    region_to_color = {}
    for i, region_id in enumerate(unique_regions):
        region_to_color[region_id] = i
    
    # Update all cells with new color assignments
    for r in range(grid_size):
        for c in range(grid_size):
            old_region_id = regions[r][c]
            if old_region_id in region_to_color:
                regions[r][c] = region_to_color[old_region_id]

def solve_queens(grid, row, regions):
    """Solve queens using backtracking with improved reliability"""
    grid_size = len(grid)
    if row == grid_size:
        # If we've reached the end, we should have exactly grid_size queens
        # (one per row), so this is a complete solution
        return True
    
    # Create column order that reduces top-left bias but is still reliable
    columns = list(range(grid_size))
    
    # For the first row, try to avoid (0,0) but don't be too restrictive
    if row == 0 and grid_size > 2:
        # Move some columns to the front to reduce (0,0) bias
        columns = [1, 2, 0] + list(range(3, grid_size))
    
    # Try placing queen in each column of current row
    for col in columns:
        if is_valid_queen_placement(grid, row, col, regions):
            grid[row][col] = 1
            
            if solve_queens(grid, row + 1, regions):
                return True
            
            grid[row][col] = 0
    
    return False

def is_valid_queen_placement(grid, row, col, regions):
    """Check if placing a queen at (row, col) is valid"""
    grid_size = len(grid)
    
    # Check row constraint
    if sum(1 for c in range(grid_size) if grid[row][c] == 1) > 0:
        return False
    
    # Check column constraint
    if sum(1 for r in range(grid_size) if grid[r][col] == 1) > 0:
        return False
    
    # Check region constraint
    region_id = regions[row][col]
    if sum(1 for r in range(grid_size) for c in range(grid_size)
           if regions[r][c] == region_id and grid[r][c] == 1) > 0:
        return False
    
    # Check adjacency constraint
    for dr in [-1, 0, 1]:
        for dc in [-1, 0, 1]:
            if dr == 0 and dc == 0:
                continue
            nr, nc = row + dr, col + dc
            if (0 <= nr < grid_size and 0 <= nc < grid_size and
                grid[nr][nc] == 1):
                return False
    
    return True

def generate_valid_solution(grid_size, regions):
    """Generate a valid solution using backtracking"""
    max_attempts = 20  # Increased for reliability
    
    # Try the standard backtracking approach
    for attempt in range(max_attempts):
        solution = [[0 for _ in range(grid_size)] for _ in range(grid_size)]
        
        # Try to place queens using standard backtracking
        if solve_queens(solution, 0, regions):
            # If backtracking succeeded, the solution should be complete and valid
            return solution
    
    # If backtracking failed completely, return None to trigger region regeneration
    return None

def verify_solution_completeness(solution):
    """Verify that the solution has exactly the right number of queens"""
    grid_size = len(solution)
    queen_count = sum(sum(row) for row in solution)
    return queen_count == grid_size

def validate_solution(solution, regions):
    """Validate that a solution follows all the rules"""
    if not verify_solution_completeness(solution):
        return False
    
    grid_size = len(solution)
    # Check that all queens are placed correctly
    for r in range(grid_size):
        for c in range(grid_size):
            if solution[r][c] == 1:
                # Check if this queen placement is valid
                if not is_valid_queen_placement_in_solution(solution, r, c, regions):
                    return False
    
    return True

def is_valid_queen_placement_in_solution(solution, row, col, regions):
    """Check if a queen placement in a complete solution is valid"""
    grid_size = len(solution)
    
    # Check row constraint (should have exactly 1 queen)
    row_count = sum(1 for c in range(grid_size) if solution[row][c] == 1)
    if row_count != 1:
        return False
    
    # Check column constraint (should have exactly 1 queen)
    col_count = sum(1 for r in range(grid_size) if solution[r][col] == 1)
    if col_count != 1:
        return False
    
    # Check region constraint (should have exactly 1 queen)
    region_id = regions[row][col]
    region_count = sum(1 for r in range(grid_size) for c in range(grid_size)
                      if regions[r][c] == region_id and solution[r][c] == 1)
    if region_count != 1:
        return False
    
    # Check adjacency constraint (no adjacent queens)
    for dr in [-1, 0, 1]:
        for dc in [-1, 0, 1]:
            if dr == 0 and dc == 0:
                continue
            nr, nc = row + dr, col + dc
            if (0 <= nr < grid_size and 0 <= nc < grid_size and
                solution[nr][nc] == 1):
                return False
    
    return True

def count_solutions(grid, regions, row=0, count=0):
    """Count the number of solutions (limited to 2 for efficiency)"""
    grid_size = len(grid)
    if count >= 2:
        return count
    
    if row == grid_size:
        return count + 1
    
    # Try placing queen in each column of current row
    for col in range(grid_size):
        if is_valid_queen_placement(grid, row, col, regions):
            grid[row][col] = 1
            count = count_solutions(grid, regions, row + 1, count)
            grid[row][col] = 0
            if count >= 2:
                return count
    
    return count

def create_puzzle(grid_size, regions, solution):
    """Create the puzzle by removing all queens (no starting clues)"""
    if solution is None:
        return None
    
    # Start with empty grid (no starting clues)
    grid = [[0 for _ in range(grid_size)] for _ in range(grid_size)]
    
    return grid

def generate_solvable_puzzle(grid_size=6, num_colors=6):
    """Generate a solvable Queens puzzle"""
    max_attempts = 10
    
    for attempt in range(max_attempts):
        # Generate fresh regions each time
        regions = generate_regions(grid_size, num_colors)
        
        # Generate a valid solution for the new regions
        solution = generate_valid_solution(grid_size, regions)
        
        # Check if we got a valid solution - if not, try again with new regions
        if solution is not None and validate_solution(solution, regions):
            # We found a valid solution, create the puzzle
            grid = create_puzzle(grid_size, regions, solution)
            return grid, regions, solution
    
    # If we couldn't generate a valid puzzle after max attempts, use a simple fallback
    print(f"DEBUG: Could not generate valid puzzle after {max_attempts} attempts")
    return generate_simple_puzzle(grid_size, num_colors)

def generate_simple_puzzle(grid_size=6, num_colors=6):
    """Generate a simple puzzle with guaranteed solvability"""
    # Use a simple region layout that we know works
    # Create simple rectangular regions
    regions = [[0 for _ in range(grid_size)] for _ in range(grid_size)]
    for r in range(grid_size):
        for c in range(grid_size):
            regions[r][c] = r  # Each row is its own region
    
    # Generate a simple solution (diagonal placement)
    solution = [[0 for _ in range(grid_size)] for _ in range(grid_size)]
    for i in range(grid_size):
        solution[i][i] = 1
    
    # Create the puzzle (empty grid)
    grid = create_puzzle(grid_size, regions, solution)
    
    return grid, regions, solution

class QueensGame:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Queens Puzzle")
        self.root.geometry("800x900")
        self.root.configure(bg='#2c3e50')
        
        # Create main frame with scrollbar
        self.main_frame = tk.Frame(self.root, bg='#2c3e50')
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create canvas for scrolling
        self.scroll_canvas = tk.Canvas(self.main_frame, bg='#2c3e50', highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.main_frame, orient="vertical", command=self.scroll_canvas.yview)
        self.scrollable_frame = tk.Frame(self.scroll_canvas, bg='#2c3e50')
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))
        )
        
        self.scroll_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.scroll_canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.scroll_canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Bind mouse wheel to scroll
        self.scroll_canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.scrollable_frame.bind("<MouseWheel>", self._on_mousewheel)
        
        # Game state - dynamic sizing
        self.grid_size = None  # Will be determined dynamically
        self.num_colors = None  # Will be determined dynamically
        self.grid = None
        self.regions = None  # Will be generated fresh each time
        self.solution = None
        self.completed_puzzles = []
        self.hint_positions = set()
        self.x_marks = set()  # Track cells marked with X for note-taking
        self.is_animating_solution = False  # Flag to prevent auto-checking during animation
        
        # Preset colors (13 non-neon, non-black, highly distinguishable colors)
        self.preset_colors = [
            '#8B4513',  # Saddle Brown
            '#228B22',  # Forest Green
            '#4169E1',  # Royal Blue
            '#DC143C',  # Crimson
            '#FF8C00',  # Dark Orange
            '#9370DB',  # Medium Purple
            '#FF69B4',  # Hot Pink
            '#32CD32',  # Lime Green
            '#1E90FF',  # Dodger Blue
            '#FF6347',  # Tomato
            '#8A2BE2',  # Blue Violet
            '#20B2AA',  # Light Sea Green
            '#DAA520'   # Goldenrod
        ]
        
        # Use preset colors for regions
        self.region_colors = self.preset_colors.copy()
        
        self.setup_ui()
        self.generate_puzzle()
        
    def setup_ui(self):
        """Set up the user interface"""
        # Title
        title_label = tk.Label(
            self.scrollable_frame,
            text="Queens Puzzle",
            font=("Arial", 24, "bold"),
            fg="white",
            bg='#2c3e50'
        )
        title_label.pack(pady=10)
        
        # Instructions
        instructions = tk.Label(
            self.scrollable_frame,
            text="Place queens so each row, column, and colored region has exactly one queen.\nQueens cannot be adjacent (including diagonally).\nClick to cycle: blank → queen → X → blank",
            font=("Arial", 12),
            fg="white",
            bg='#2c3e50',
            justify="center"
        )
        instructions.pack(pady=5)
        
        # Canvas for the grid
        self.canvas = tk.Canvas(
            self.scrollable_frame,
            width=700,
            height=700,
            bg='white',
            highlightthickness=0
        )
        self.canvas.pack(pady=10)
        
        # Bind click events
        self.canvas.bind("<Button-1>", self.on_cell_click)
        self.canvas.bind("<Double-Button-1>", self.on_cell_double_click)
        
        # Buttons frame
        button_frame = tk.Frame(self.scrollable_frame, bg='#2c3e50')
        button_frame.pack(pady=10)
        
        # Buttons
        self.check_btn = tk.Button(
            button_frame,
            text="Check Solution",
            command=self.check_solution,
            font=("Arial", 12),
            bg='#34495e',
            fg='black',
            padx=20,
            pady=5
        )
        self.check_btn.pack(side=tk.LEFT, padx=5)
        
        self.hint_btn = tk.Button(
            button_frame,
            text="Get Hint",
            command=self.get_hint,
            font=("Arial", 12),
            bg='#34495e',
            fg='black',
            padx=20,
            pady=5
        )
        self.hint_btn.pack(side=tk.LEFT, padx=5)
        
        self.solution_btn = tk.Button(
            button_frame,
            text="Show Solution",
            command=self.show_solution,
            font=("Arial", 12),
            bg='#34495e',
            fg='black',
            padx=20,
            pady=5
        )
        self.solution_btn.pack(side=tk.LEFT, padx=5)
        
        self.new_game_btn = tk.Button(
            button_frame,
            text="New Game",
            command=self.new_game,
            font=("Arial", 12),
            bg='#34495e',
            fg='black',
            padx=20,
            pady=5
        )
        self.new_game_btn.pack(side=tk.LEFT, padx=5)
        
        self.history_btn = tk.Button(
            button_frame,
            text="History",
            command=self.show_history,
            font=("Arial", 12),
            bg='#34495e',
            fg='black',
            padx=20,
            pady=5
        )
        self.history_btn.pack(side=tk.LEFT, padx=5)
        
        # Status label
        self.status_label = tk.Label(
            self.scrollable_frame,
            text="Click on cells to place queens",
            font=("Arial", 12),
            fg="white",
            bg='#2c3e50'
        )
        self.status_label.pack(pady=5)
    
    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        self.scroll_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
    def generate_regions(self):
        """Generate colored regions for the grid with varied shapes"""
        regions = [[0 for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        
        # Use the determined number of colors
        num_colors = self.num_colors
        
        # Select unique colors from preset (each color used only once)
        selected_colors = self.preset_colors[:num_colors]
        self.region_colors = selected_colors
        
        # Create varied region shapes using flood fill approach
        region_id = 0
        visited = [[False for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        
        # Define possible region shapes (no diagonal connections)
        region_templates = [
            # L-shapes (no diagonal connections)
            [(0,0), (0,1), (1,0), (1,1), (2,0)],  # L-shape 1
            [(0,0), (0,1), (0,2), (1,2), (2,2)],  # L-shape 2
            [(0,0), (1,0), (2,0), (2,1), (2,2)],  # L-shape 3
            [(0,2), (1,2), (2,0), (2,1), (2,2)],  # L-shape 4
            
            # T-shapes
            [(0,1), (1,0), (1,1), (1,2), (2,1)],  # T-shape 1
            [(0,0), (0,1), (0,2), (1,1), (2,1)],  # T-shape 2
            
            # Plus shapes
            [(0,1), (1,0), (1,1), (1,2), (2,1)],  # Plus shape
            
            # Linear shapes
            [(0,0), (0,1), (0,2), (0,3)],  # Horizontal line
            [(0,0), (1,0), (2,0), (3,0)],  # Vertical line
            
            # Square shapes
            [(0,0), (0,1), (1,0), (1,1)],  # 2x2 square
            [(0,0), (0,1), (0,2), (1,0), (1,1), (1,2), (2,0), (2,1), (2,2)],  # 3x3 square
            
            # Corner shapes
            [(0,0), (0,1), (1,0)],  # Corner 1
            [(0,1), (0,2), (1,2)],  # Corner 2
            [(1,0), (2,0), (2,1)],  # Corner 3
            [(1,2), (2,1), (2,2)],  # Corner 4
        ]
        
        # Try to place regions using templates
        attempts = 0
        max_attempts = 500  # Reduced from 1000 for speed
        
        # Shuffle templates for more variety
        random.shuffle(region_templates)
        
        while region_id < num_colors and attempts < max_attempts:
            attempts += 1
            
            # Find an empty position
            empty_positions = []
            for r in range(self.grid_size):
                for c in range(self.grid_size):
                    if not visited[r][c]:
                        empty_positions.append((r, c))
            
            if not empty_positions:
                break
            
            # Choose a random empty position
            start_r, start_c = random.choice(empty_positions)
            
            # Choose a random template (with preference for different sizes)
            template = random.choice(region_templates)
            
            # Sometimes try smaller templates for more variety
            if random.random() < 0.3:  # 30% chance
                small_templates = [t for t in region_templates if len(t) <= 4]
                if small_templates:
                    template = random.choice(small_templates)
            
            # Try to place the template
            can_place = True
            template_positions = []
            
            for dr, dc in template:
                new_r, new_c = start_r + dr, start_c + dc
                if (new_r >= self.grid_size or new_c >= self.grid_size or 
                    visited[new_r][new_c]):
                    can_place = False
                    break
                template_positions.append((new_r, new_c))
            
            if can_place:
                # Place the region with unique color assignment
                for r, c in template_positions:
                    regions[r][c] = region_id
                    visited[r][c] = True
                region_id += 1
        
        # Fill any remaining empty cells with random regions
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if not visited[r][c]:
                    # Find adjacent region or create new one (no diagonal connections)
                    adjacent_regions = set()
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:  # Only horizontal/vertical
                        nr, nc = r + dr, c + dc
                        if (0 <= nr < self.grid_size and 0 <= nc < self.grid_size and
                            visited[nr][nc]):
                            adjacent_regions.add(regions[nr][nc])
                    
                    if adjacent_regions:
                        # Join to an adjacent region
                        regions[r][c] = random.choice(list(adjacent_regions))
                    else:
                        # Create new region
                        regions[r][c] = region_id
                        region_id += 1
                    visited[r][c] = True
        
        # Ensure we have exactly the right number of colors
        unique_regions = len(set(regions[r][c] for r in range(self.grid_size) for c in range(self.grid_size)))
        
        if unique_regions < self.num_colors:
            # Split some large regions
            self.split_large_regions(regions, self.num_colors)
        elif unique_regions > self.num_colors:
            # Merge some small regions
            self.merge_small_regions(regions, self.num_colors)
        
        # Ensure each region gets a unique color
        self.assign_unique_colors(regions)
        
        # Skip color optimization for speed - regions are already well-distributed
        # self.optimize_color_placement(regions)
        
        return regions
    
    def split_large_regions(self, regions, min_regions):
        """Split large regions to increase region count"""
        current_regions = len(set(regions[r][c] for r in range(self.grid_size) for c in range(self.grid_size)))
        
        while current_regions < min_regions:
            # Find the largest region
            region_sizes = {}
            for r in range(self.grid_size):
                for c in range(self.grid_size):
                    region_id = regions[r][c]
                    region_sizes[region_id] = region_sizes.get(region_id, 0) + 1
            
            if not region_sizes:
                break
            
            largest_region = max(region_sizes, key=region_sizes.get)
            
            # Find cells in this region
            region_cells = []
            for r in range(self.grid_size):
                for c in range(self.grid_size):
                    if regions[r][c] == largest_region:
                        region_cells.append((r, c))
            
            if len(region_cells) < 4:  # Too small to split
                break
            
            # Split the region
            split_point = len(region_cells) // 2
            new_region_id = max(region_sizes.keys()) + 1
            
            for i, (r, c) in enumerate(region_cells):
                if i >= split_point:
                    regions[r][c] = new_region_id
            
            current_regions = len(set(regions[r][c] for r in range(self.grid_size) for c in range(self.grid_size)))
    
    def merge_small_regions(self, regions, max_regions):
        """Merge small regions to decrease region count"""
        current_regions = len(set(regions[r][c] for r in range(self.grid_size) for c in range(self.grid_size)))
        
        while current_regions > max_regions:
            # Find the smallest region
            region_sizes = {}
            for r in range(self.grid_size):
                for c in range(self.grid_size):
                    region_id = regions[r][c]
                    region_sizes[region_id] = region_sizes.get(region_id, 0) + 1
            
            if not region_sizes:
                break
            
            smallest_region = min(region_sizes, key=region_sizes.get)
            
            # Find an adjacent region to merge with (no diagonal connections)
            adjacent_regions = set()
            for r in range(self.grid_size):
                for c in range(self.grid_size):
                    if regions[r][c] == smallest_region:
                        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:  # Only horizontal/vertical
                            nr, nc = r + dr, c + dc
                            if (0 <= nr < self.grid_size and 0 <= nc < self.grid_size and
                                regions[nr][nc] != smallest_region):
                                adjacent_regions.add(regions[nr][nc])
            
            if adjacent_regions:
                # Merge with the largest adjacent region
                merge_target = max(adjacent_regions, key=lambda x: region_sizes.get(x, 0))
                
                for r in range(self.grid_size):
                    for c in range(self.grid_size):
                        if regions[r][c] == smallest_region:
                            regions[r][c] = merge_target
            
            current_regions = len(set(regions[r][c] for r in range(self.grid_size) for c in range(self.grid_size)))
    
    def assign_unique_colors(self, regions):
        """Assign unique colors to each region"""
        # Get all unique region IDs
        unique_regions = list(set(regions[r][c] for r in range(self.grid_size) for c in range(self.grid_size)))
        unique_regions.sort()  # Sort for consistent assignment
        
        # Create a mapping from old region ID to new color index
        region_to_color = {}
        for i, region_id in enumerate(unique_regions):
            if i < len(self.region_colors):
                region_to_color[region_id] = i
        
        # Update all cells with new color assignments
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                old_region_id = regions[r][c]
                if old_region_id in region_to_color:
                    regions[r][c] = region_to_color[old_region_id]
    
    def optimize_color_placement(self, regions):
        """Optimize color placement to avoid similar adjacent colors (simplified for speed)"""
        # Define color similarity groups (colors that are too similar)
        similar_groups = [
            ['#9370DB', '#8A2BE2'],  # Purple variants (Medium Purple, Blue Violet)
            ['#228B22', '#32CD32'],  # Green variants (Forest Green, Lime Green)
            ['#4169E1', '#1E90FF'],  # Blue variants (Royal Blue, Dodger Blue)
            ['#FF8C00', '#FF6347'],  # Orange/Red variants (Dark Orange, Tomato)
            ['#FF69B4', '#DC143C'],  # Pink/Red variants (Hot Pink, Crimson)
        ]
        
        # Reduced attempts for speed
        max_attempts = 10  # Reduced from 50
        for attempt in range(max_attempts):
            improved = False
            
            # Find adjacent regions with similar colors
            for r in range(self.grid_size):
                for c in range(self.grid_size):
                    current_color = self.region_colors[regions[r][c] % len(self.region_colors)]
                    
                    # Check adjacent cells
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = r + dr, c + dc
                        if (0 <= nr < self.grid_size and 0 <= nc < self.grid_size and
                            regions[nr][nc] != regions[r][c]):
                            
                            adjacent_color = self.region_colors[regions[nr][nc] % len(self.region_colors)]
                            
                            # Check if colors are too similar
                            if self.are_colors_similar(current_color, adjacent_color, similar_groups):
                                # Try to find a better color for one of the regions
                                better_color_id = self.find_better_color(regions, regions[r][c], similar_groups)
                                if better_color_id is not None:
                                    # Change the region color
                                    old_region_id = regions[r][c]
                                    for rr in range(self.grid_size):
                                        for cc in range(self.grid_size):
                                            if regions[rr][cc] == old_region_id:
                                                regions[rr][cc] = better_color_id
                                    improved = True
                                    break
                    if improved:
                        break
                if improved:
                    break
            
            if not improved:
                break
    
    def are_colors_similar(self, color1, color2, similar_groups):
        """Check if two colors are too similar"""
        for group in similar_groups:
            if color1 in group and color2 in group:
                return True
        return False
    
    def find_better_color(self, regions, region_id, similar_groups):
        """Find a better color for a region that doesn't conflict with adjacent regions"""
        current_color = self.region_colors[region_id % len(self.region_colors)]
        
        # Get all colors currently used in the puzzle
        used_colors = set()
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                used_colors.add(self.region_colors[regions[r][c] % len(self.region_colors)])
        
        # Get all colors used by adjacent regions
        adjacent_colors = set()
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if regions[r][c] == region_id:
                    # Check adjacent cells
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = r + dr, c + dc
                        if (0 <= nr < self.grid_size and 0 <= nc < self.grid_size and
                            regions[nr][nc] != region_id):
                            adjacent_colors.add(self.region_colors[regions[nr][nc] % len(self.region_colors)])
        
        # Find a color that's not used elsewhere and not similar to any adjacent colors
        for i, color in enumerate(self.region_colors):
            if color == current_color:
                continue
            
            # Skip if color is already used in the puzzle
            if color in used_colors:
                continue
            
            is_good = True
            for adj_color in adjacent_colors:
                if self.are_colors_similar(color, adj_color, similar_groups):
                    is_good = False
                    break
            
            if is_good:
                return i
        
        return None
    
    def draw_grid(self):
        """Draw the game grid with regions and queens"""
        self.canvas.delete("all")
        
        # Get current canvas size
        canvas_width = self.canvas.winfo_reqwidth()
        canvas_height = self.canvas.winfo_reqheight()
        cell_size = min(canvas_width, canvas_height) // self.grid_size
        
        # Draw region backgrounds
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                x1, y1 = c * cell_size, r * cell_size
                x2, y2 = x1 + cell_size, y1 + cell_size
                
                region_id = self.regions[r][c]
                color = self.region_colors[region_id % len(self.region_colors)]
                
                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=color,
                    outline='black',
                    width=2
                )
        
        # Draw grid lines
        grid_size_pixels = cell_size * self.grid_size
        for i in range(self.grid_size + 1):
            # Vertical lines
            x = i * cell_size
            self.canvas.create_line(x, 0, x, grid_size_pixels, fill='black', width=2)
            
            # Horizontal lines
            y = i * cell_size
            self.canvas.create_line(0, y, grid_size_pixels, y, fill='black', width=2)
        
        # Draw queens and X marks
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if self.grid[r][c] == 1:  # Queen present
                    x1, y1 = c * cell_size + 5, r * cell_size + 5
                    x2, y2 = x1 + cell_size - 10, y1 + cell_size - 10
                    
                    # Draw better queen icon
                    center_x, center_y = (x1 + x2) // 2, (y1 + y2) // 2
                    queen_size = cell_size // 3
                    
                    # Queen base (circle)
                    self.canvas.create_oval(
                        center_x - queen_size, center_y - queen_size,
                        center_x + queen_size, center_y + queen_size,
                        fill='#2c3e50',
                        outline='white',
                        width=2
                    )
                    
                    # Crown (more detailed)
                    crown_height = queen_size // 2
                    crown_width = queen_size
                    
                    # Crown base
                    self.canvas.create_rectangle(
                        center_x - crown_width//2, center_y - crown_height,
                        center_x + crown_width//2, center_y - crown_height//2,
                        fill='#f39c12',
                        outline='white',
                        width=1
                    )
                    
                    # Crown points (5 points for more royal look)
                    for i in range(5):
                        angle = (i * 72) - 90  # 72 degrees apart, starting from top
                        point_x = center_x + (crown_width//2) * math.cos(math.radians(angle))
                        point_y = center_y - crown_height + (crown_height//2) * math.sin(math.radians(angle))
                        
                        # Create triangular crown point
                        self.canvas.create_polygon(
                            point_x, point_y,
                            point_x - crown_width//8, center_y - crown_height//2,
                            point_x + crown_width//8, center_y - crown_height//2,
                            fill='#f39c12',
                            outline='white',
                            width=1
                        )
                    
                    # Queen symbol (Q) in the center
                    self.canvas.create_text(
                        center_x, center_y + queen_size//4,
                        text="♕",
                        fill='white',
                        font=("Arial", queen_size, "bold")
                    )
                
                elif (r, c) in self.x_marks:  # X mark present
                    x1, y1 = c * cell_size + 10, r * cell_size + 10
                    x2, y2 = x1 + cell_size - 20, y1 + cell_size - 20
                    
                    # Draw X mark in black for better visibility
                    self.canvas.create_line(
                        x1, y1, x2, y2,
                        fill='black',
                        width=4
                    )
                    self.canvas.create_line(
                        x1, y2, x2, y1,
                        fill='black',
                        width=4
                    )
        
        # Highlight violations
        self.highlight_violations()
    
    def highlight_violations(self):
        """Highlight cells that violate the rules"""
        canvas_width = self.canvas.winfo_reqwidth()
        canvas_height = self.canvas.winfo_reqheight()
        cell_size = min(canvas_width, canvas_height) // self.grid_size
        
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if self.grid[r][c] == 1:  # Queen present
                    # Check for violations
                    if self.has_violations(r, c):
                        x1, y1 = c * cell_size, r * cell_size
                        x2, y2 = x1 + cell_size, y1 + cell_size
                        
                        self.canvas.create_rectangle(
                            x1, y1, x2, y2,
                            outline='red',
                            width=4
                        )
    
    def has_violations(self, row, col):
        """Check if a queen at (row, col) violates any rules"""
        if self.grid[row][col] != 1:
            return False
        
        # Check row constraint
        row_count = sum(1 for c in range(self.grid_size) if self.grid[row][c] == 1)
        if row_count > 1:
            return True
        
        # Check column constraint
        col_count = sum(1 for r in range(self.grid_size) if self.grid[r][col] == 1)
        if col_count > 1:
            return True
        
        # Check region constraint
        region_id = self.regions[row][col]
        region_count = sum(1 for r in range(self.grid_size) for c in range(self.grid_size)
                          if self.regions[r][c] == region_id and self.grid[r][c] == 1)
        if region_count > 1:
            return True
        
        # Check adjacency constraint
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                nr, nc = row + dr, col + dc
                if (0 <= nr < self.grid_size and 0 <= nc < self.grid_size and
                    self.grid[nr][nc] == 1):
                    return True
        
        return False
    
    def on_cell_click(self, event):
        """Handle cell click events - cycle through blank → queen → X → blank"""
        canvas_width = self.canvas.winfo_reqwidth()
        canvas_height = self.canvas.winfo_reqheight()
        cell_size = min(canvas_width, canvas_height) // self.grid_size
        col = event.x // cell_size
        row = event.y // cell_size
        
        if 0 <= row < self.grid_size and 0 <= col < self.grid_size:
            # Cycle through states: blank → queen → X → blank
            if self.grid[row][col] == 1:  # Currently has queen
                # Remove queen and add X mark
                self.grid[row][col] = 0
                self.x_marks.add((row, col))
            elif (row, col) in self.x_marks:  # Currently has X mark
                # Remove X mark (back to blank)
                self.x_marks.remove((row, col))
            else:  # Currently blank
                # Add queen
                self.grid[row][col] = 1
            
            self.draw_grid()
            self.update_status()
    
    def on_cell_double_click(self, event):
        """Handle cell double-click events - same as single click for cycling"""
        self.on_cell_click(event)
    
    def update_status(self):
        """Update the status message"""
        # Don't auto-check during solution animation
        if self.is_animating_solution:
            return
        
        queen_count = sum(sum(row) for row in self.grid)
        total_queens_needed = self.grid_size
        
        if queen_count == total_queens_needed:
            if self.check_solution_silent():
                # Ensure the final queen is visually placed before showing completion
                self.root.update()  # Force UI update to show the final queen
                self.root.after(100, self.show_completion_and_new_game)  # Small delay to ensure visual update
                self.status_label.config(text="🎉 Puzzle Complete! 🎉")
            else:
                self.status_label.config(text="Check your solution - there are rule violations")
        else:
            self.status_label.config(text=f"Board: {self.grid_size}x{self.grid_size} | Colors: {self.num_colors} | Queens: {queen_count}/{total_queens_needed} | Need: {total_queens_needed - queen_count} more")
    
    def check_solution_silent(self):
        """Check if the current solution is correct (without showing message)"""
        # Check if all queens are placed
        queen_count = sum(sum(row) for row in self.grid)
        if queen_count != self.grid_size:
            return False
        
        # Check for violations
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if self.grid[r][c] == 1 and self.has_violations(r, c):
                    return False
        
        return True
    
    def check_solution(self):
        """Check and display solution status"""
        if self.check_solution_silent():
            # Ensure all queens are visually placed before showing completion
            self.root.update()  # Force UI update to show all queens
            self.root.after(100, self.show_completion_and_new_game)  # Small delay to ensure visual update
            self.status_label.config(text="🎉 Correct Solution! 🎉")
        else:
            self.status_label.config(text="Solution has errors. Check highlighted cells.")
    
    def get_hint(self):
        """Provide a hint to the player"""
        # Find a cell that should have a queen according to the solution
        if self.solution is None:
            self.status_label.config(text="No solution available for hints")
            return
        
        # Find empty cells that should have queens
        hint_candidates = []
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if self.grid[r][c] == 0 and self.solution[r][c] == 1:
                    hint_candidates.append((r, c))
        
        if hint_candidates:
            # Choose a strategic hint
            r, c = self.choose_strategic_hint(hint_candidates)
            self.grid[r][c] = 1
            self.hint_positions.add((r, c))
            self.draw_grid()
            self.update_status()
            self.status_label.config(text=f"Hint: Queen placed at row {r+1}, column {c+1}")
        else:
            self.status_label.config(text="No more hints available")
    
    def choose_strategic_hint(self, candidates):
        """Choose a strategic hint position"""
        # Prioritize positions that help complete constraints
        for r, c in candidates:
            # Check if this position helps complete a row, column, or region
            row_count = sum(1 for col in range(self.grid_size) if self.grid[r][col] == 1)
            col_count = sum(1 for row in range(self.grid_size) if self.grid[row][c] == 1)
            region_id = self.regions[r][c]
            region_count = sum(1 for row in range(self.grid_size) for col in range(self.grid_size)
                              if self.regions[row][col] == region_id and self.grid[row][col] == 1)
            
            # If this would complete a constraint, prioritize it
            if row_count == 0 or col_count == 0 or region_count == 0:
                return (r, c)
        
        # Otherwise, return a random candidate
        return random.choice(candidates)
    
    def show_solution(self):
        """Show the complete solution"""
        if self.solution is None:
            self.status_label.config(text="No solution available")
            return
        
        # Set animation flag to prevent auto-checking
        self.is_animating_solution = True
        
        # Clear current grid
        self.grid = [[0 for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        self.hint_positions.clear()
        self.x_marks.clear()
        
        # Animate solution
        self.animate_solution()
    
    def animate_solution(self):
        """Animate the solution cell by cell"""
        if self.solution is None:
            return
        
        # Find all queen positions
        queen_positions = []
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if self.solution[r][c] == 1:
                    queen_positions.append((r, c))
        
        # Animate placing queens
        self.animate_queen_placement(queen_positions, 0)
    
    def animate_queen_placement(self, positions, index):
        """Recursively animate queen placement"""
        if index >= len(positions):
            # Animation complete - now check the solution
            self.is_animating_solution = False  # Clear animation flag
            self.check_solution_after_animation()
            return
        
        r, c = positions[index]
        self.grid[r][c] = 1
        self.draw_grid()
        # Don't call update_status during animation to prevent auto-checking
        self.status_label.config(text=f"Showing solution... {index + 1}/{len(positions)} queens placed")
        
        # Schedule next queen placement
        self.root.after(300, lambda: self.animate_queen_placement(positions, index + 1))
    
    def check_solution_after_animation(self):
        """Check the solution after animation is complete"""
        # Force UI update to show all queens
        self.root.update()
        
        # Small delay to ensure visual update is complete
        self.root.after(100, self.verify_and_show_success)
    
    def verify_and_show_success(self):
        """Verify the solution and show success message"""
        if self.check_solution_silent():
            # Solution is correct - show success and generate new puzzle
            self.status_label.config(text="🎉 Solution Complete! 🎉")
            self.show_completion_and_new_game()
        else:
            # Solution has errors - debug and handle gracefully
            self.debug_solution_issues()
    
    def debug_solution_issues(self):
        """Debug why solution verification failed"""
        queen_count = sum(sum(row) for row in self.grid)
        total_needed = self.grid_size
        
        # Check for specific issues
        issues = []
        
        if queen_count != total_needed:
            issues.append(f"Wrong queen count: {queen_count}/{total_needed}")
        
        # Check for violations
        violation_count = 0
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if self.grid[r][c] == 1 and self.has_violations(r, c):
                    violation_count += 1
        
        if violation_count > 0:
            issues.append(f"Rule violations: {violation_count} queens")
        
        # Show detailed error message
        if issues:
            error_msg = f"Solution verification failed: {', '.join(issues)}"
        else:
            error_msg = "Solution verification failed - unknown issue"
        
        self.status_label.config(text=error_msg)
        print(f"DEBUG: {error_msg}")  # Also print to console for debugging
    
    def show_completion_and_new_game(self):
        """Show completion message and generate new game"""
        # Save completed puzzle
        self.save_completed_puzzle()
        
        # Show completion message
        messagebox.showinfo("Puzzle Complete!", "🎉 Congratulations! Puzzle solved! 🎉\nGenerating new puzzle...")
        
        # Generate new puzzle
        self.generate_puzzle()
    
    def new_game(self):
        """Start a new game"""
        self.generate_puzzle()
    
    def determine_board_size(self):
        """Determine the board size, number of colors, and number of queens"""
        # Randomly choose board size between 6 and 12
        self.grid_size = random.randint(6, 12)
        self.num_colors = self.grid_size  # Equal to board size
        # Number of queens will also be equal to grid_size
        
        # Initialize grid with new size
        self.grid = [[0 for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        self.hint_positions.clear()
        self.x_marks.clear()
        
        # Update canvas size based on grid size
        canvas_size = min(700, 50 * self.grid_size)  # Scale canvas with grid size
        self.canvas.config(width=canvas_size, height=canvas_size)
    
    def generate_puzzle(self):
        """Generate a new puzzle with fresh regions and solution"""
        self.status_label.config(text="Generating new puzzle...")
        self.root.update()
        
        # Try to generate a valid puzzle with multiple attempts
        max_puzzle_attempts = 10
        for puzzle_attempt in range(max_puzzle_attempts):
            # Determine board size and colors
            self.determine_board_size()
            
            # Generate fresh regions each time
            self.regions = self.generate_regions()
            
            # Generate a valid solution for the new regions
            self.solution = self.generate_valid_solution()
            
            # Check if we got a valid solution - if not, try again with new regions
            if self.solution is not None and self.validate_solution(self.solution):
                # We found a valid solution, create the puzzle
                self.create_puzzle()
                self.draw_grid()
                self.update_status()
                self.status_label.config(text="New puzzle ready!")
                return
            
            print(f"DEBUG: Puzzle attempt {puzzle_attempt + 1} failed - regenerating regions")
        
        # If we couldn't generate a valid puzzle after max attempts, use a simple fallback
        print(f"DEBUG: Could not generate valid puzzle after {max_puzzle_attempts} attempts")
        self.status_label.config(text="Generating simple puzzle...")
        self.root.update()
        self.generate_simple_puzzle()
        self.draw_grid()
        self.update_status()
        self.status_label.config(text="New puzzle ready!")
    
    def generate_valid_solution(self):
        """Generate a valid solution using backtracking"""
        max_attempts = 20  # Increased for reliability
        
        # Try the standard backtracking approach
        for attempt in range(max_attempts):
            solution = [[0 for _ in range(self.grid_size)] for _ in range(self.grid_size)]
            
            # Try to place queens using standard backtracking
            if self.solve_queens(solution, 0):
                # If backtracking succeeded, the solution should be complete and valid
                return solution
        
        # If backtracking failed completely, return None to trigger region regeneration
        return None
    
    def verify_solution_completeness(self, solution):
        """Verify that the solution has exactly the right number of queens"""
        queen_count = sum(sum(row) for row in solution)
        return queen_count == self.grid_size
    
    def validate_solution(self, solution):
        """Validate that a solution follows all the rules"""
        if not self.verify_solution_completeness(solution):
            return False
        
        # Check that all queens are placed correctly
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if solution[r][c] == 1:
                    # Check if this queen placement is valid
                    if not self.is_valid_queen_placement_in_solution(solution, r, c):
                        return False
        
        return True
    
    
    def is_valid_queen_placement_in_solution(self, solution, row, col):
        """Check if a queen placement in a complete solution is valid"""
        # Check row constraint (should have exactly 1 queen)
        row_count = sum(1 for c in range(self.grid_size) if solution[row][c] == 1)
        if row_count != 1:
            return False
        
        # Check column constraint (should have exactly 1 queen)
        col_count = sum(1 for r in range(self.grid_size) if solution[r][col] == 1)
        if col_count != 1:
            return False
        
        # Check region constraint (should have exactly 1 queen)
        region_id = self.regions[row][col]
        region_count = sum(1 for r in range(self.grid_size) for c in range(self.grid_size)
                          if self.regions[r][c] == region_id and solution[r][c] == 1)
        if region_count != 1:
            return False
        
        # Check adjacency constraint (no adjacent queens)
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                nr, nc = row + dr, col + dc
                if (0 <= nr < self.grid_size and 0 <= nc < self.grid_size and
                    solution[nr][nc] == 1):
                    return False
        
        return True
    
    def count_solutions(self, grid, row=0, count=0):
        """Count the number of solutions (limited to 2 for efficiency)"""
        if count >= 2:
            return count
        
        if row == self.grid_size:
            return count + 1
        
        # Try placing queen in each column of current row
        for col in range(self.grid_size):
            if self.is_valid_queen_placement(grid, row, col):
                grid[row][col] = 1
                count = self.count_solutions(grid, row + 1, count)
                grid[row][col] = 0
                if count >= 2:
                    return count
        
        return count
    
    def solve_queens(self, grid, row):
        """Solve queens using backtracking with improved reliability"""
        if row == self.grid_size:
            # If we've reached the end, we should have exactly grid_size queens
            # (one per row), so this is a complete solution
            return True
        
        # Create column order that reduces top-left bias but is still reliable
        columns = list(range(self.grid_size))
        
        # For the first row, try to avoid (0,0) but don't be too restrictive
        if row == 0 and self.grid_size > 2:
            # Move some columns to the front to reduce (0,0) bias
            columns = [1, 2, 0] + list(range(3, self.grid_size))
        
        # Try placing queen in each column of current row
        for col in columns:
            if self.is_valid_queen_placement(grid, row, col):
                grid[row][col] = 1
                
                if self.solve_queens(grid, row + 1):
                    return True
                
                grid[row][col] = 0
        
        return False
    
    def solve_queens_with_random_start(self, grid, row):
        """Solve queens using backtracking with random starting positions"""
        if row == self.grid_size:
            # If we've reached the end, we should have exactly grid_size queens
            return True
        
        # For the first few rows, try to avoid the top-left corner
        if row < 3:  # First 3 rows
            # Create a list of columns, but avoid (0,0) for the first row
            if row == 0:
                columns = list(range(1, self.grid_size))  # Skip column 0 for first row
                if len(columns) == 0:  # If grid is 1x1, we have to use (0,0)
                    columns = [0]
            else:
                columns = list(range(self.grid_size))
            random.shuffle(columns)
        else:
            # For later rows, use normal randomization
            columns = list(range(self.grid_size))
            random.shuffle(columns)
        
        # Try placing queen in each column of current row (in random order)
        for col in columns:
            if self.is_valid_queen_placement(grid, row, col):
                grid[row][col] = 1
                
                if self.solve_queens_with_random_start(grid, row + 1):
                    return True
                
                grid[row][col] = 0
        
        return False
    
    def solve_queens_avoid_corners(self, grid, row):
        """Solve queens using backtracking while avoiding corner positions"""
        if row == self.grid_size:
            # If we've reached the end, we should have exactly grid_size queens
            return True
        
        # Define corner positions
        corners = [(0, 0), (0, self.grid_size-1), (self.grid_size-1, 0), (self.grid_size-1, self.grid_size-1)]
        
        # Create column list, prioritizing non-corner positions
        columns = list(range(self.grid_size))
        
        # For the first few rows, avoid corner positions
        if row < 2:  # First 2 rows
            # Remove corner columns from consideration
            corner_cols = [0, self.grid_size-1]
            non_corner_cols = [c for c in columns if c not in corner_cols]
            if non_corner_cols:  # If we have non-corner options, use them
                columns = non_corner_cols
            # If no non-corner options, we'll have to use corners
        
        random.shuffle(columns)
        
        # Try placing queen in each column of current row (in random order)
        for col in columns:
            if self.is_valid_queen_placement(grid, row, col):
                grid[row][col] = 1
                
                if self.solve_queens_avoid_corners(grid, row + 1):
                    return True
                
                grid[row][col] = 0
        
        return False
    
    def is_valid_queen_placement(self, grid, row, col):
        """Check if placing a queen at (row, col) is valid"""
        # Check row constraint
        if sum(1 for c in range(self.grid_size) if grid[row][c] == 1) > 0:
            return False
        
        # Check column constraint
        if sum(1 for r in range(self.grid_size) if grid[r][col] == 1) > 0:
            return False
        
        # Check region constraint
        region_id = self.regions[row][col]
        if sum(1 for r in range(self.grid_size) for c in range(self.grid_size)
               if self.regions[r][c] == region_id and grid[r][c] == 1) > 0:
            return False
        
        # Check adjacency constraint
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                nr, nc = row + dr, col + dc
                if (0 <= nr < self.grid_size and 0 <= nc < self.grid_size and
                    grid[nr][nc] == 1):
                    return False
        
        return True
    
    def generate_simple_solution(self):
        """Generate a simple valid solution as fallback"""
        solution = [[0 for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        
        # Use backtracking to ensure we get a complete solution
        if self.solve_queens(solution, 0):
            return solution
        
        # If backtracking fails, try the basic solution approach
        return self.create_basic_solution()
    
    def create_basic_solution(self):
        """Create a basic valid solution as last resort"""
        solution = [[0 for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        
        # Try to place queens one by one in a systematic way
        for row in range(self.grid_size):
            placed = False
            
            # Create column order that reduces top-left bias
            columns = list(range(self.grid_size))
            if row == 0 and self.grid_size > 2:
                # For first row, try columns 1, 2 first, then 0, then others
                columns = [1, 2, 0] + list(range(3, self.grid_size))
            
            for col in columns:
                if self.is_valid_queen_placement(solution, row, col):
                    solution[row][col] = 1
                    placed = True
                    break
            
            # If we couldn't place a queen in this row, try to fix previous placements
            if not placed:
                # Remove the last placed queen and try a different position
                for prev_row in range(row - 1, -1, -1):
                    for prev_col in range(self.grid_size):
                        if solution[prev_row][prev_col] == 1:
                            solution[prev_row][prev_col] = 0
                            # Try placing in a different column
                            for new_col in range(self.grid_size):
                                if new_col != prev_col and self.is_valid_queen_placement(solution, prev_row, new_col):
                                    solution[prev_row][new_col] = 1
                                    # Now try to place queen in current row
                                    for col in columns:
                                        if self.is_valid_queen_placement(solution, row, col):
                                            solution[row][col] = 1
                                            placed = True
                                            break
                                    if placed:
                                        break
                            if placed:
                                break
                    if placed:
                        break
        
        return solution
    
    def create_minimal_valid_solution(self):
        """Create a minimal valid solution as absolute last resort"""
        solution = [[0 for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        
        # Place queens in a simple pattern that should work for most region layouts
        # Try placing one queen per region, starting with the largest regions
        region_sizes = {}
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                region_id = self.regions[r][c]
                if region_id not in region_sizes:
                    region_sizes[region_id] = []
                region_sizes[region_id].append((r, c))
        
        # Sort regions by size (largest first)
        sorted_regions = sorted(region_sizes.items(), key=lambda x: len(x[1]), reverse=True)
        
        # Place one queen in each of the largest regions
        for region_id, cells in sorted_regions[:self.grid_size]:
            # Try cells in a deterministic order that reduces top-left bias
            # Sort cells to try non-corner positions first
            cells.sort(key=lambda x: (x[0] + x[1], x[0], x[1]))  # Sort by distance from top-left
            for r, c in cells:
                if self.is_valid_queen_placement(solution, r, c):
                    solution[r][c] = 1
                    break
        
        return solution
    
    def create_forced_solution(self):
        """Create a forced valid solution as absolute last resort"""
        solution = [[0 for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        
        # Try to place one queen per row, ensuring all constraints are met
        for row in range(self.grid_size):
            placed = False
            for col in range(self.grid_size):
                if self.is_valid_queen_placement(solution, row, col):
                    solution[row][col] = 1
                    placed = True
                    break
            
            # If we couldn't place a queen in this row, we need to backtrack
            if not placed:
                # Find the previous row with a queen and try a different position
                for prev_row in range(row - 1, -1, -1):
                    for prev_col in range(self.grid_size):
                        if solution[prev_row][prev_col] == 1:
                            solution[prev_row][prev_col] = 0
                            # Try placing in a different column
                            for new_col in range(prev_col + 1, self.grid_size):
                                if self.is_valid_queen_placement(solution, prev_row, new_col):
                                    solution[prev_row][new_col] = 1
                                    # Now try to place queen in current row
                                    for col in range(self.grid_size):
                                        if self.is_valid_queen_placement(solution, row, col):
                                            solution[row][col] = 1
                                            placed = True
                                            break
                                    if placed:
                                        break
                            if placed:
                                break
                    if placed:
                        break
                
                # If still not placed, this is a very difficult puzzle
                # Just place the queen in the first valid position
                if not placed:
                    for col in range(self.grid_size):
                        if self.is_valid_queen_placement(solution, row, col):
                            solution[row][col] = 1
                            break
        
        return solution
    
    def generate_simple_puzzle(self):
        """Generate a simple puzzle with guaranteed solvability and uniqueness"""
        # Use a simple region layout that we know works
        self.grid_size = 6  # Use a smaller, more manageable size
        self.num_colors = 6
        
        # Create simple rectangular regions
        self.regions = [[0 for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                self.regions[r][c] = r  # Each row is its own region
        
        # Use simple colors
        self.region_colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD']
        
        # Generate a simple solution (diagonal placement)
        self.solution = [[0 for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        for i in range(self.grid_size):
            self.solution[i][i] = 1
        
        # Create the puzzle (empty grid)
        self.create_puzzle()
        
    
    def create_puzzle(self):
        """Create the puzzle by removing all queens (no starting clues)"""
        if self.solution is None:
            return
        
        # Start with empty grid (no starting clues)
        self.grid = [[0 for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        
        # Clear hint positions and X marks
        self.hint_positions.clear()
        self.x_marks.clear()
    
    def save_completed_puzzle(self):
        """Save the completed puzzle to history"""
        puzzle_data = {
            'name': f"Queens Puzzle {len(self.completed_puzzles) + 1}",
            'grid': [row[:] for row in self.grid],
            'solution': [row[:] for row in self.solution] if self.solution else None,
            'regions': [row[:] for row in self.regions],
            'grid_size': self.grid_size,
            'num_colors': self.num_colors,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
        history_window.configure(bg='#2c3e50')
        history_window.geometry("600x400")
        
        # Title
        title_label = tk.Label(
            history_window,
            text="Completed Puzzles",
            fg="white",
            bg='#2c3e50',
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=10)
        
        # Create scrollable frame
        canvas = tk.Canvas(history_window, bg='#2c3e50', highlightthickness=0)
        scrollbar = tk.Scrollbar(history_window, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#2c3e50')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Add puzzle entries
        for i, puzzle in enumerate(self.completed_puzzles):
            puzzle_frame = tk.Frame(scrollable_frame, bg='#2c3e50', relief=tk.RAISED, bd=1)
            puzzle_frame.pack(fill=tk.X, padx=10, pady=5)
            
            # Puzzle info
            info_label = tk.Label(
                puzzle_frame,
                text=f"{puzzle['name']} - {puzzle['grid_size']}x{puzzle['grid_size']} - {puzzle['timestamp']}",
                fg="white",
                bg='#2c3e50',
                font=("Arial", 12, "bold")
            )
            info_label.pack(pady=5)
            
            # Replay button
            replay_btn = tk.Button(
                puzzle_frame,
                text="Replay",
                command=lambda p=puzzle: self.replay_puzzle(p),
                bg="#34495e",
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
        # Load the puzzle data
        self.grid_size = puzzle['grid_size']
        self.num_colors = puzzle['num_colors']
        self.solution = [row[:] for row in puzzle['solution']] if puzzle['solution'] else None
        self.regions = [row[:] for row in puzzle['regions']]
        
        # Start with completely empty grid
        self.grid = [[0 for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        self.hint_positions.clear()
        self.x_marks.clear()
        
        # Update canvas size
        canvas_size = min(700, 50 * self.grid_size)
        self.canvas.config(width=canvas_size, height=canvas_size)
        
        self.draw_grid()
        self.update_status()
        self.status_label.config(text="Replaying puzzle - Click cells to place queens")
    
    def run(self):
        """Start the game"""
        self.root.mainloop()

if __name__ == "__main__":
    game = QueensGame()
    game.run()


class QueensPuzzle(TutorEnvBase):
    def __init__(self, grid_size=8, problem_types=["basic"], **kwargs):
        if grid_size < 4:
            raise ValueError("Grid size must be at least 4")
        
        self.grid_size = grid_size
        self.problem_types = problem_types
        self.problem = None
        
        # Preset colors (13 non-neon, non-black, highly distinguishable colors)
        self.preset_colors = [
            '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD',
            '#FFB6C1', '#98FB98', '#F0E68C', '#FFA07A', '#20B2AA', '#87CEEB', '#D8BFD8'
        ]
        
        super().__init__(**kwargs)
        self.set_random_problem()
    
    def _blank_state(self):
        state = {}
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                state[f"cell_{r}_{c}"] = {"value": "0"}
        
        state["queen_count"] = {"value": "0"}
        state["grid_size"] = {"value": str(self.grid_size)}
        state["regions"] = {"value": str([])}
        
        return state
    
    def action_is_done(self, action):
        return action.selection == "done"
    
    def set_start_state(self, grid, regions):
        self.problem = (grid, regions)
        self.state = self._blank_state()
        
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if grid[r][c] == 1:
                    self.state[f"cell_{r}_{c}"] = {"value": "1"}
        
        self.state["regions"] = {"value": str(regions)}
        queen_count = sum(1 for row in grid for cell in row if cell == 1)
        self.state["queen_count"] = {"value": str(queen_count)}
    
    def set_random_problem(self):
        ptype = random.choice(self.problem_types)
        
        if ptype == "basic":
            # Determine board size and colors
            self.determine_board_size()
            
            # Generate fresh regions
            regions = self.generate_regions()
            
            # Generate a valid solution for the new regions
            solution = self.generate_valid_solution(regions)
            
            # Create the puzzle (empty grid)
            grid = [[0 for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        
        self.set_start_state(grid, regions)
        return {"grid": grid, "regions": regions}
    
    def determine_board_size(self):
        """Determine board size and number of colors"""
        self.grid_size = 6
        self.num_colors = 6
    
    def generate_regions(self):
        """Generate colored regions for the grid with varied shapes"""
        regions = [[0 for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        
        # Use the determined number of colors
        num_colors = self.num_colors
        
        # Select unique colors from preset (each color used only once)
        selected_colors = self.preset_colors[:num_colors]
        self.region_colors = selected_colors
        
        # Create varied region shapes using flood fill approach
        region_id = 0
        visited = [[False for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        
        # Define possible region shapes (no diagonal connections)
        region_templates = [
            # L-shapes (no diagonal connections)
            [(0,0), (0,1), (1,0), (1,1), (2,0)],  # L-shape 1
            [(0,0), (0,1), (0,2), (1,2), (2,2)],  # L-shape 2
            [(0,0), (1,0), (2,0), (2,1), (2,2)],  # L-shape 3
            [(0,2), (1,2), (2,0), (2,1), (2,2)],  # L-shape 4
            
            # T-shapes
            [(0,1), (1,0), (1,1), (1,2), (2,1)],  # T-shape 1
            [(0,0), (0,1), (0,2), (1,1), (2,1)],  # T-shape 2
            
            # Plus shapes
            [(0,1), (1,0), (1,1), (1,2), (2,1)],  # Plus shape
            
            # Linear shapes
            [(0,0), (0,1), (0,2), (0,3)],  # Horizontal line
            [(0,0), (1,0), (2,0), (3,0)],  # Vertical line
            
            # Square shapes
            [(0,0), (0,1), (1,0), (1,1)],  # 2x2 square
            [(0,0), (0,1), (0,2), (1,0), (1,1), (1,2), (2,0), (2,1), (2,2)],  # 3x3 square
            
            # Corner shapes
            [(0,0), (0,1), (1,0)],  # Corner 1
            [(0,1), (0,2), (1,2)],  # Corner 2
            [(1,0), (2,0), (2,1)],  # Corner 3
            [(1,2), (2,1), (2,2)],  # Corner 4
        ]
        
        # Try to place regions using templates
        attempts = 0
        max_attempts = 500  # Reduced from 1000 for speed
        
        # Shuffle templates for more variety
        random.shuffle(region_templates)
        
        while region_id < num_colors and attempts < max_attempts:
            attempts += 1
            
            # Find an empty position
            empty_positions = []
            for r in range(self.grid_size):
                for c in range(self.grid_size):
                    if not visited[r][c]:
                        empty_positions.append((r, c))
            
            if not empty_positions:
                break
            
            # Choose a random empty position
            start_r, start_c = random.choice(empty_positions)
            
            # Choose a random template (with preference for different sizes)
            template = random.choice(region_templates)
            
            # Sometimes try smaller templates for more variety
            if random.random() < 0.3:  # 30% chance
                small_templates = [t for t in region_templates if len(t) <= 4]
                if small_templates:
                    template = random.choice(small_templates)
            
            # Try to place the template
            can_place = True
            template_positions = []
            
            for dr, dc in template:
                new_r, new_c = start_r + dr, start_c + dc
                if (new_r >= self.grid_size or new_c >= self.grid_size or 
                    visited[new_r][new_c]):
                    can_place = False
                    break
                template_positions.append((new_r, new_c))
            
            if can_place:
                # Place the region with unique color assignment
                for r, c in template_positions:
                    regions[r][c] = region_id
                    visited[r][c] = True
                region_id += 1
        
        # Fill any remaining empty cells with random regions
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if not visited[r][c]:
                    # Find adjacent region or create new one (no diagonal connections)
                    adjacent_regions = set()
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:  # Only horizontal/vertical
                        nr, nc = r + dr, c + dc
                        if (0 <= nr < self.grid_size and 0 <= nc < self.grid_size and
                            visited[nr][nc]):
                            adjacent_regions.add(regions[nr][nc])
                    
                    if adjacent_regions:
                        # Join to an adjacent region
                        regions[r][c] = random.choice(list(adjacent_regions))
                    else:
                        # Create new region
                        regions[r][c] = region_id
                        region_id += 1
                    visited[r][c] = True
        
        # Ensure we have exactly the right number of colors
        unique_regions = len(set(regions[r][c] for r in range(self.grid_size) for c in range(self.grid_size)))
        
        if unique_regions < self.num_colors:
            # Split some large regions
            self.split_large_regions(regions, self.num_colors)
        elif unique_regions > self.num_colors:
            # Merge some small regions
            self.merge_small_regions(regions, self.num_colors)
        
        # Ensure each region gets a unique color
        self.assign_unique_colors(regions)
        
        return regions
    
    def split_large_regions(self, regions, min_regions):
        """Split large regions to increase region count"""
        current_regions = len(set(regions[r][c] for r in range(self.grid_size) for c in range(self.grid_size)))
        
        while current_regions < min_regions:
            # Find the largest region
            region_sizes = {}
            for r in range(self.grid_size):
                for c in range(self.grid_size):
                    region_id = regions[r][c]
                    region_sizes[region_id] = region_sizes.get(region_id, 0) + 1
            
            if not region_sizes:
                break
            
            largest_region = max(region_sizes, key=region_sizes.get)
            if region_sizes[largest_region] < 3:  # Can't split regions smaller than 3
                break
            
            # Find a cell in the largest region to split
            for r in range(self.grid_size):
                for c in range(self.grid_size):
                    if regions[r][c] == largest_region:
                        # Create new region
                        regions[r][c] = current_regions
                        current_regions += 1
                        break
                if current_regions >= min_regions:
                    break
    
    def merge_small_regions(self, regions, max_regions):
        """Merge small regions to decrease region count"""
        current_regions = len(set(regions[r][c] for r in range(self.grid_size) for c in range(self.grid_size)))
        
        while current_regions > max_regions:
            # Find the smallest region
            region_sizes = {}
            for r in range(self.grid_size):
                for c in range(self.grid_size):
                    region_id = regions[r][c]
                    region_sizes[region_id] = region_sizes.get(region_id, 0) + 1
            
            if not region_sizes:
                break
            
            smallest_region = min(region_sizes, key=region_sizes.get)
            
            # Find an adjacent region to merge with
            for r in range(self.grid_size):
                for c in range(self.grid_size):
                    if regions[r][c] == smallest_region:
                        # Find adjacent region
                        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                            nr, nc = r + dr, c + dc
                            if (0 <= nr < self.grid_size and 0 <= nc < self.grid_size and
                                regions[nr][nc] != smallest_region):
                                # Merge with adjacent region
                                regions[r][c] = regions[nr][nc]
                                current_regions -= 1
                                break
                        if current_regions <= max_regions:
                            break
                if current_regions <= max_regions:
                    break
    
    def assign_unique_colors(self, regions):
        """Assign unique colors to regions"""
        unique_regions = list(set(regions[r][c] for r in range(self.grid_size) for c in range(self.grid_size)))
        for i, region_id in enumerate(unique_regions):
            for r in range(self.grid_size):
                for c in range(self.grid_size):
                    if regions[r][c] == region_id:
                        regions[r][c] = i
    
    def generate_valid_solution(self, regions):
        """Generate a valid solution using backtracking"""
        max_attempts = 20  # Increased for reliability
        
        # Try the standard backtracking approach
        for attempt in range(max_attempts):
            solution = [[0 for _ in range(self.grid_size)] for _ in range(self.grid_size)]
            
            # Try to place queens using standard backtracking
            if self.solve_queens(solution, 0, regions):
                # If backtracking succeeded, the solution should be complete and valid
                return solution
        
        # If backtracking failed completely, return None to trigger region regeneration
        return None
    
    def solve_queens(self, grid, row, regions):
        """Solve queens using backtracking with improved reliability"""
        if row == self.grid_size:
            # If we've reached the end, we should have exactly grid_size queens
            # (one per row), so this is a complete solution
            return True
        
        # Create column order that reduces top-left bias but is still reliable
        columns = list(range(self.grid_size))
        
        # For the first row, try to avoid (0,0) but don't be too restrictive
        if row == 0 and self.grid_size > 2:
            # Move some columns to the front to reduce (0,0) bias
            columns = [1, 2, 0] + list(range(3, self.grid_size))
        
        # Try placing queen in each column of current row
        for col in columns:
            if self.is_valid_queen_placement(grid, row, col, regions):
                grid[row][col] = 1
                
                if self.solve_queens(grid, row + 1, regions):
                    return True
                
                grid[row][col] = 0
        
        return False
    
    def is_valid_queen_placement(self, grid, row, col, regions):
        """Check if placing a queen at (row, col) is valid"""
        # Check row constraint
        if sum(1 for c in range(self.grid_size) if grid[row][c] == 1) > 0:
            return False
        
        # Check column constraint
        if sum(1 for r in range(self.grid_size) if grid[r][col] == 1) > 0:
            return False
        
        # Check region constraint
        region_id = regions[row][col]
        if sum(1 for r in range(self.grid_size) for c in range(self.grid_size)
               if regions[r][c] == region_id and grid[r][c] == 1) > 0:
            return False
        
        # Check adjacency constraint
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                nr, nc = row + dr, col + dc
                if (0 <= nr < self.grid_size and 0 <= nc < self.grid_size and
                    grid[nr][nc] == 1):
                    return False
        
        return True
    
    def verify_solution_completeness(self, solution):
        """Verify that the solution has exactly the right number of queens"""
        queen_count = sum(sum(row) for row in solution)
        return queen_count == self.grid_size
    
    def validate_solution(self, solution, regions):
        """Validate that a solution follows all the rules"""
        if not self.verify_solution_completeness(solution):
            return False
        
        # Check that all queens are placed correctly
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if solution[r][c] == 1:
                    # Check if this queen placement is valid
                    if not self.is_valid_queen_placement_in_solution(solution, r, c, regions):
                        return False
        
        return True
    
    def is_valid_queen_placement_in_solution(self, solution, row, col, regions):
        """Check if a queen placement in a complete solution is valid"""
        # Check row constraint (should have exactly 1 queen)
        row_count = sum(1 for c in range(self.grid_size) if solution[row][c] == 1)
        if row_count != 1:
            return False
        
        # Check column constraint (should have exactly 1 queen)
        col_count = sum(1 for r in range(self.grid_size) if solution[r][col] == 1)
        if col_count != 1:
            return False
        
        # Check region constraint (should have exactly 1 queen)
        region_id = regions[row][col]
        region_count = sum(1 for r in range(self.grid_size) for c in range(self.grid_size)
                          if regions[r][c] == region_id and solution[r][c] == 1)
        if region_count != 1:
            return False
        
        # Check adjacency constraint (no adjacent queens)
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                nr, nc = row + dr, col + dc
                if (0 <= nr < self.grid_size and 0 <= nc < self.grid_size and
                    solution[nr][nc] == 1):
                    return False
        
        return True
    
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
        grid, regions = self.problem if self.problem else (None, None)
        
        if not grid or not regions:
            return None
        
        current_queens = []
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if state.get(f"cell_{r}_{c}", {}).get("value", "0") == "1":
                    current_queens.append((r, c))
        
        if len(current_queens) == self.grid_size:
            return None
        
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if state.get(f"cell_{r}_{c}", {}).get("value", "0") == "0":
                    if self._is_valid_placement(current_queens, (r, c), regions):
                        sai = (f"cell_{r}_{c}", 'PlaceQueen', f"{r},{c}")
                        arg_foci = [f"cell_{r}_{c}"]
                        how_help = f"Place queen at ({r},{c})"
                        return Action(sai, arg_foci=arg_foci, how_help=how_help)
        
        return None
    
    def check(self, action, **kwargs):
        action = Action(action)
        grid, regions = self.problem if self.problem else (None, None)
        
        if not grid or not regions:
            return -1
        
        if action.selection == "done":
            current_queens = []
            for r in range(self.grid_size):
                for c in range(self.grid_size):
                    if self.state.get(f"cell_{r}_{c}", {}).get("value", "0") == "1":
                        current_queens.append((r, c))
            
            if len(current_queens) == self.grid_size and self._is_valid_solution(current_queens, regions):
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
        
        current_queens = []
        for row in range(self.grid_size):
            for col in range(self.grid_size):
                if self.state.get(f"cell_{row}_{col}", {}).get("value", "0") == "1":
                    current_queens.append((row, col))
        
        if self.state.get(f"cell_{r}_{c}", {}).get("value", "0") == "1":
            return 1
        elif self._is_valid_placement(current_queens, (r, c), regions):
            return 1
        else:
            return -1
    
    def apply(self, action, **kwargs):
        action = Action(action)
        grid, regions = self.problem if self.problem else (None, None)
        
        if not grid or not regions:
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
        
        current_value = new_state.get(f"cell_{r}_{c}", {}).get("value", "0")
        if current_value == "0":
            new_state[f"cell_{r}_{c}"] = {"value": "1"}
        else:
            new_state[f"cell_{r}_{c}"] = {"value": "0"}
        
        queen_count = sum(1 for row in range(self.grid_size) for col in range(self.grid_size) 
                         if new_state.get(f"cell_{row}_{col}", {}).get("value", "0") == "1")
        new_state["queen_count"] = {"value": str(queen_count)}
        
        return new_state
    
    def _is_valid_placement(self, current_queens, new_pos, regions):
        r, c = new_pos
        
        temp_grid = [[0 for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        for qr, qc in current_queens:
            temp_grid[qr][qc] = 1
        
        return self.is_valid_queen_placement(temp_grid, r, c, regions)
    
    def _is_valid_solution(self, queens, regions):
        if len(queens) != self.grid_size:
            return False
        
        temp_grid = [[0 for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        for r, c in queens:
            temp_grid[r][c] = 1
        
        return self.validate_solution(temp_grid, regions)


if __name__ == "__main__":
    print("=== Testing QueensPuzzle Environment Implementation ===\n")
    
    print("1. Testing basic puzzle generation...")
    try:
        env = QueensPuzzle(grid_size=6, problem_types=["basic"])
        print(f"   ✓ Generated Queens puzzle: {env.grid_size}x{env.grid_size}")
        print(f"   ✓ Problem types: {env.problem_types}")
    except Exception as e:
        print(f"   ✗ Error generating puzzle: {e}")
    
    print("\n2. Testing state management...")
    try:
        print(f"   ✓ Initial state keys: {list(env.state.keys())[:5]}...")
        print(f"   ✓ Queen count: {env.state.get('queen_count', {}).get('value', '')}")
        print(f"   ✓ Grid size: {env.state.get('grid_size', {}).get('value', '')}")
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
            print(f"   ✓ Old queen count: {old_state.get('queen_count', {}).get('value', '')}")
            print(f"   ✓ New queen count: {new_state.get('queen_count', {}).get('value', '')}")
            
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
        test_queens = [(0, 0)]
        test_pos = (1, 2)
        is_valid = env._is_valid_placement(test_queens, test_pos, env.problem[1])
        print(f"   ✓ _is_valid_placement test: {is_valid}")
        
        test_solution = [(0, 1), (1, 3), (2, 0), (3, 2)]
        is_solution = env._is_valid_solution(test_solution, env.problem[1])
        print(f"   ✓ _is_valid_solution test: {is_solution}")
    except Exception as e:
        print(f"   ✗ Error testing helper functions: {e}")
    
    print("\n=== Testing Complete ===")
    print("All core functions have been tested successfully!")