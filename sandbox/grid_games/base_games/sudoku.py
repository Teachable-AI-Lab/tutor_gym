# sudoku.py
# 9x9 Sudoku puzzle game in Python (Tkinter)
# Run: python sudoku.py

import tkinter as tk
from tkinter import messagebox
import random
import datetime

# Game constants
CELL_SIZE = 50
GAP = 1
PADDING = 20
BG_COLOR = "#1a1a1a"
GRID_BG = "#2d2d2d"
CELL_BG = "#3a3a3a"
HINT_BG = "#4a4a4a"
TEXT_COLOR = "#ffffff"
BORDER_COLOR = "#555555"
SELECTED_COLOR = "#4a90e2"
ERROR_COLOR = "#ff6b6b"
CORRECT_COLOR = "#4ecdc4"

class SudokuGame:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Sudoku - 9x9 Puzzle Game")
        self.root.configure(bg=BG_COLOR)
        self.root.resizable(False, False)
        
        # Game state
        self.grid_size = 9
        self.grid = [[0 for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        self.solution = None
        self.completed_puzzles = []
        self.hint_positions = set()  # Track which cells are hints (cannot be changed)
        self.selected_cell = None
        self.notes_mode = False  # Track if we're in notes mode
        self.notes = {}  # Dictionary to store notes for each cell: (r, c) -> set of numbers
        self.showing_solution = False  # Track if we're showing the solution
        self.user_input = {}  # Store original user input: (r, c) -> number
        self.corrected_cells = set()  # Track cells showing correct answer instead of user input
        
        self.setup_ui()
        self.generate_puzzle()
        
    def setup_ui(self):
        """Setup the user interface"""
        # Title
        self.title_label = tk.Label(
            self.root, 
            text="Sudoku 9x9", 
            fg=TEXT_COLOR, 
            bg=BG_COLOR, 
            font=("Arial", 20, "bold")
        )
        self.title_label.pack(pady=10)
        
        # Instructions
        self.instructions = tk.Label(
            self.root,
            text="Fill the grid with numbers 1-9. Each row, column, and 3x3 box must contain all numbers 1-9",
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
        
        # Bind events
        self.canvas.bind("<Button-1>", self.on_cell_click)
        self.root.bind("<Key>", self.on_key_press)
        self.canvas.focus_set()
        
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
        
        self.instant_solve_btn = tk.Button(
            self.button_frame,
            text="Instant Solve",
            command=self.instant_solution,
            bg="#4a4a4a",
            fg="black",
            font=("Arial", 12, "bold"),
            padx=20,
            pady=5
        )
        self.solve_btn.pack(side=tk.LEFT, padx=5)
        self.instant_solve_btn.pack(side=tk.LEFT, padx=5)
        
        self.notes_btn = tk.Button(
            self.button_frame,
            text="Notes",
            command=self.toggle_notes_mode,
            bg="#4a4a4a",
            fg="black",
            font=("Arial", 12, "bold"),
            padx=20,
            pady=5
        )
        self.notes_btn.pack(side=tk.LEFT, padx=5)
        
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
            text="Click cells to select, type numbers 1-9 to fill",
            fg=TEXT_COLOR,
            bg=BG_COLOR,
            font=("Arial", 12)
        )
        self.status_label.pack(pady=5)
        
    def generate_puzzle(self):
        """Generate a new Sudoku puzzle"""
        # Clear the grid
        self.grid = [[0 for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        self.hint_positions = set()
        self.selected_cell = None
        self.notes = {}  # Clear notes
        self.notes_mode = False  # Reset notes mode
        self.showing_solution = False  # Reset solution display
        self.user_input = {}  # Clear user input tracking
        self.corrected_cells = set()  # Clear corrected cells tracking
        
        # Generate a valid solution first
        self.solution = self.generate_valid_solution()
        
        # Create the puzzle by removing some numbers
        self.create_puzzle()
        
        self.draw_grid()
    
    def toggle_notes_mode(self):
        """Toggle between normal mode and notes mode"""
        self.notes_mode = not self.notes_mode
        
        # Update button appearance
        if self.notes_mode:
            self.notes_btn.config(bg="#2a4d2a", text="Notes ON")
            self.status_label.config(text="Notes mode: Select cells and type numbers 1-9 to add/remove notes")
        else:
            self.notes_btn.config(bg="#4a4a4a", text="Notes")
            self.status_label.config(text="Click cells to select, type numbers 1-9 to fill")
        
        self.draw_grid()
        
    def generate_valid_solution(self):
        """Generate a valid Sudoku solution with complex patterns"""
        max_attempts = 10
        for attempt in range(max_attempts):
            solution = [[0 for _ in range(self.grid_size)] for _ in range(self.grid_size)]
            
            # Start with a more complex base pattern instead of simple sequential filling
            self.create_complex_base_pattern(solution)
            
            # Apply transformations to create variety
            self.apply_solution_transformations(solution)
            
            # Fill remaining cells using backtracking
            if self.solve_sudoku(solution):
                # Verify the solution is complete and valid
                if self.is_complete_solution(solution):
                    return solution
        
        # Fallback: generate a simple valid solution
        return self.generate_simple_solution()
    
    def is_complete_solution(self, grid):
        """Check if the grid is a complete, valid Sudoku solution"""
        # Check if all cells are filled
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if grid[r][c] == 0:
                    return False
        
        # Check if solution is valid
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                num = grid[r][c]
                # Temporarily remove the number to check validity
                grid[r][c] = 0
                if not self.is_valid_move(grid, r, c, num):
                    grid[r][c] = num
                    return False
                grid[r][c] = num
        
        return True
    
    def generate_simple_solution(self):
        """Generate a simple but valid Sudoku solution as fallback"""
        solution = [[0 for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        
        # Fill diagonal 3x3 boxes first (they don't interfere with each other)
        for box in range(0, 9, 3):
            numbers = list(range(1, 10))
            random.shuffle(numbers)
            for i in range(3):
                for j in range(3):
                    solution[box + i][box + j] = numbers[i * 3 + j]
        
        # Fill remaining cells using backtracking
        self.solve_sudoku(solution)
        
        return solution
    
    def create_complex_base_pattern(self, grid):
        """Create a complex base pattern for the solution"""
        # Fill diagonal 3x3 boxes first (they don't interfere with each other)
        for box in range(0, 9, 3):
            self.fill_diagonal_box(grid, box, box)
        
        # Apply some strategic placements
        self.add_strategic_placements(grid)
    
    def fill_diagonal_box(self, grid, start_row, start_col):
        """Fill a 3x3 box with a complex pattern"""
        # Create a shuffled list of numbers 1-9
        numbers = list(range(1, 10))
        random.shuffle(numbers)
        
        # Fill the box with the shuffled numbers
        for i in range(3):
            for j in range(3):
                grid[start_row + i][start_col + j] = numbers[i * 3 + j]
    
    def add_strategic_placements(self, grid):
        """Add some strategic number placements to create complexity"""
        # Add some numbers in non-diagonal positions to create interesting patterns
        for _ in range(15):  # Add 15 strategic numbers
            row = random.randint(0, 8)
            col = random.randint(0, 8)
            
            # Skip if already filled or in diagonal boxes
            if grid[row][col] != 0:
                continue
            if (row // 3) == (col // 3):  # Skip diagonal boxes
                continue
            
            # Try to place a valid number
            for num in range(1, 10):
                if self.is_valid_move(grid, row, col, num):
                    grid[row][col] = num
                    break
    
    def apply_solution_transformations(self, grid):
        """Apply transformations to create more complex solutions"""
        # Randomly swap rows within the same 3x3 block
        for block in range(3):
            start_row = block * 3
            rows = [start_row, start_row + 1, start_row + 2]
            random.shuffle(rows)
            
            # Swap rows if it maintains validity
            if self.is_valid_row_swap(grid, rows[0], rows[1]):
                self.swap_rows(grid, rows[0], rows[1])
            if self.is_valid_row_swap(grid, rows[1], rows[2]):
                self.swap_rows(grid, rows[1], rows[2])
        
        # Randomly swap columns within the same 3x3 block
        for block in range(3):
            start_col = block * 3
            cols = [start_col, start_col + 1, start_col + 2]
            random.shuffle(cols)
            
            # Swap columns if it maintains validity
            if self.is_valid_col_swap(grid, cols[0], cols[1]):
                self.swap_columns(grid, cols[0], cols[1])
            if self.is_valid_col_swap(grid, cols[1], cols[2]):
                self.swap_columns(grid, cols[1], cols[2])
    
    def is_valid_row_swap(self, grid, row1, row2):
        """Check if swapping two rows maintains validity"""
        # Rows in the same 3x3 block can be swapped
        return (row1 // 3) == (row2 // 3)
    
    def is_valid_col_swap(self, grid, col1, col2):
        """Check if swapping two columns maintains validity"""
        # Columns in the same 3x3 block can be swapped
        return (col1 // 3) == (col2 // 3)
    
    def swap_rows(self, grid, row1, row2):
        """Swap two rows in the grid"""
        grid[row1], grid[row2] = grid[row2], grid[row1]
    
    def swap_columns(self, grid, col1, col2):
        """Swap two columns in the grid"""
        for row in range(9):
            grid[row][col1], grid[row][col2] = grid[row][col2], grid[row][col1]
    
    def solve_sudoku(self, grid):
        """Solve Sudoku using backtracking"""
        for row in range(self.grid_size):
            for col in range(self.grid_size):
                if grid[row][col] == 0:
                    # Try numbers 1-9
                    for num in range(1, 10):
                        if self.is_valid_move(grid, row, col, num):
                            grid[row][col] = num
                            if self.solve_sudoku(grid):
                                return True
                            grid[row][col] = 0
                    return False
        return True
    
    def is_valid_move(self, grid, row, col, num):
        """Check if placing num at (row, col) is valid"""
        # Check row
        for c in range(self.grid_size):
            if grid[row][c] == num:
                return False
        
        # Check column
        for r in range(self.grid_size):
            if grid[r][col] == num:
                return False
        
        # Check 3x3 box
        box_row = (row // 3) * 3
        box_col = (col // 3) * 3
        for r in range(box_row, box_row + 3):
            for c in range(box_col, box_col + 3):
                if grid[r][c] == num:
                    return False
        
        return True
    
    def create_puzzle(self):
        """Create the puzzle by removing some numbers"""
        # Start with the full solution
        self.grid = [row[:] for row in self.solution]
        
        # Determine difficulty (remove 40-60 numbers)
        cells_to_remove = random.randint(40, 60)
        
        # Get all cell positions
        all_cells = [(r, c) for r in range(self.grid_size) for c in range(self.grid_size)]
        random.shuffle(all_cells)
        
        # Remove numbers while ensuring the puzzle remains solvable
        removed_count = 0
        for r, c in all_cells:
            if removed_count >= cells_to_remove:
                break
            
            # Store the original number
            original_num = self.grid[r][c]
            self.grid[r][c] = 0
            
            # Check if the puzzle is still solvable
            temp_grid = [row[:] for row in self.grid]
            if self.count_solutions(temp_grid) == 1:
                removed_count += 1
            else:
                # Restore the number if it makes the puzzle unsolvable
                self.grid[r][c] = original_num
        
        # Ensure no 3x3 block is completely filled with hints
        self.ensure_no_complete_blocks()
        
        # Final validation: ensure puzzle is still solvable
        temp_grid = [row[:] for row in self.grid]
        if self.count_solutions(temp_grid) != 1:
            # If puzzle is not solvable, regenerate it
            self.status_label.config(text="Regenerating puzzle for solvability...")
            self.root.update()
            self.generate_puzzle()
            return
        
        # Mark remaining numbers as hints
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if self.grid[r][c] != 0:
                    self.hint_positions.add((r, c))
    
    def ensure_no_complete_blocks(self):
        """Ensure no 3x3 block is completely filled with hints"""
        for box_row in range(3):
            for box_col in range(3):
                # Count hints in this 3x3 block
                hint_count = 0
                hint_positions = []
                
                for r in range(box_row * 3, box_row * 3 + 3):
                    for c in range(box_col * 3, box_col * 3 + 3):
                        if self.grid[r][c] != 0:
                            hint_count += 1
                            hint_positions.append((r, c))
                
                # If block has 8 or 9 hints, remove some to make it more challenging
                if hint_count >= 8:
                    # Remove 2-3 hints from this block, but check solvability
                    hints_to_remove = min(3, hint_count - 5)  # Keep at least 5 hints
                    
                    # Try to remove hints while maintaining solvability
                    removed = 0
                    for r, c in hint_positions:
                        if removed >= hints_to_remove:
                            break
                        
                        # Store the original number
                        original_num = self.grid[r][c]
                        self.grid[r][c] = 0
                        
                        # Check if puzzle is still solvable
                        temp_grid = [row[:] for row in self.grid]
                        if self.count_solutions(temp_grid) == 1:
                            removed += 1
                        else:
                            # Restore the number if it makes puzzle unsolvable
                            self.grid[r][c] = original_num
    
    def count_solutions(self, grid, count=0):
        """Count the number of solutions (limited to 2 for efficiency)"""
        if count >= 2:
            return count
        
        for row in range(self.grid_size):
            for col in range(self.grid_size):
                if grid[row][col] == 0:
                    for num in range(1, 10):
                        if self.is_valid_move(grid, row, col, num):
                            grid[row][col] = num
                            count = self.count_solutions(grid, count)
                            grid[row][col] = 0
                            if count >= 2:
                                return count
                    return count
        return count + 1
    
    def draw_grid(self):
        """Draw the Sudoku grid with enhanced 3x3 demarcations"""
        self.canvas.delete("all")
        
        # Draw 3x3 box backgrounds first for better visual separation
        for box_row in range(3):
            for box_col in range(3):
                x1 = box_col * 3 * (CELL_SIZE + GAP) + GAP
                y1 = box_row * 3 * (CELL_SIZE + GAP) + GAP
                x2 = x1 + 3 * (CELL_SIZE + GAP) - GAP
                y2 = y1 + 3 * (CELL_SIZE + GAP) - GAP
                
                # Alternate box background colors for better visibility
                if (box_row + box_col) % 2 == 0:
                    box_bg = "#2a2a2a"  # Slightly darker
                else:
                    box_bg = "#2d2d2d"  # Standard grid color
                
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=box_bg, outline="", width=0)
        
        # Draw individual cells
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                x1 = c * (CELL_SIZE + GAP) + GAP
                y1 = r * (CELL_SIZE + GAP) + GAP
                x2 = x1 + CELL_SIZE
                y2 = y1 + CELL_SIZE
                
                # Determine cell color
                if (r, c) == self.selected_cell:
                    fill_color = SELECTED_COLOR
                elif (r, c) in self.hint_positions:
                    fill_color = HINT_BG
                elif (self.showing_solution and (r, c) in self.user_input and 
                      self.user_input[(r, c)] != self.solution[r][c]):
                    fill_color = ERROR_COLOR  # Red background for incorrect cells
                else:
                    fill_color = CELL_BG
                
                # Draw cell background
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=fill_color, outline="", width=0)
                
                # Draw number if present
                if self.grid[r][c] != 0:
                    center_x = (x1 + x2) // 2
                    center_y = (y1 + y2) // 2
                    
                    # Determine text color based on mode and correctness
                    if (r, c) in self.hint_positions:
                        text_color = TEXT_COLOR
                    elif (self.showing_solution and (r, c) in self.user_input and 
                          self.user_input[(r, c)] != self.solution[r][c]):
                        text_color = "white"  # White text on red background
                    else:
                        text_color = CORRECT_COLOR
                    
                    self.canvas.create_text(center_x, center_y, text=str(self.grid[r][c]), 
                                          fill=text_color, font=("Arial", 16, "bold"))
                
                # Draw notes if present and cell is empty
                elif (r, c) in self.notes and self.notes[(r, c)]:
                    self.draw_notes(r, c, x1, y1, x2, y2)
        
        # Draw enhanced 3x3 box borders with thicker lines
        for i in range(4):  # 4 lines (0, 3, 6, 9)
            x = i * 3 * (CELL_SIZE + GAP) + GAP
            y = i * 3 * (CELL_SIZE + GAP) + GAP
            
            # Vertical lines
            self.canvas.create_line(x, GAP, x, 9 * (CELL_SIZE + GAP) - GAP, 
                                  fill="#ffffff", width=4)
            
            # Horizontal lines
            self.canvas.create_line(GAP, y, 9 * (CELL_SIZE + GAP) - GAP, y, 
                                  fill="#ffffff", width=4)
        
        # Draw thin cell borders
        for r in range(self.grid_size + 1):
            for c in range(self.grid_size + 1):
                x = c * (CELL_SIZE + GAP) + GAP
                y = r * (CELL_SIZE + GAP) + GAP
                
                # Only draw thin borders if not on 3x3 boundaries
                if r % 3 != 0:  # Not on 3x3 horizontal boundary
                    self.canvas.create_line(x, y, x + 9 * (CELL_SIZE + GAP) - GAP, y, 
                                          fill=BORDER_COLOR, width=1)
                
                if c % 3 != 0:  # Not on 3x3 vertical boundary
                    self.canvas.create_line(x, y, x, y + 9 * (CELL_SIZE + GAP) - GAP, 
                                          fill=BORDER_COLOR, width=1)
    
    def draw_notes(self, r, c, x1, y1, x2, y2):
        """Draw notes in a 3x3 grid within the cell"""
        if (r, c) not in self.notes or not self.notes[(r, c)]:
            return
        
        # Calculate positions for 3x3 grid of notes
        cell_width = x2 - x1
        cell_height = y2 - y1
        note_size = min(cell_width, cell_height) // 3
        
        # Determine note color based on selection
        if (r, c) == self.selected_cell:
            note_color = "black"
        else:
            note_color = "#888888"
        
        # Draw each note number in its position
        for num in sorted(self.notes[(r, c)]):
            # Calculate position in 3x3 grid (1-9 -> 0-8 -> row, col)
            note_row = (num - 1) // 3
            note_col = (num - 1) % 3
            
            # Calculate actual position
            note_x = x1 + note_col * note_size + note_size // 2
            note_y = y1 + note_row * note_size + note_size // 2
            
            # Draw the note number
            self.canvas.create_text(note_x, note_y, text=str(num), 
                                  fill=note_color, font=("Arial", 8, "bold"))
    
    def on_cell_click(self, event):
        """Handle cell click events"""
        # Calculate which cell was clicked
        c = event.x // (CELL_SIZE + GAP)
        r = event.y // (CELL_SIZE + GAP)
        
        if 0 <= r < self.grid_size and 0 <= c < self.grid_size:
            # Don't allow selecting hint positions
            if (r, c) in self.hint_positions:
                self.status_label.config(text="Cannot select hint positions!")
                return
            
            # Check if we're in solution mode and clicking on an incorrect cell
            if (self.showing_solution and (r, c) in self.user_input and 
                self.user_input[(r, c)] != self.solution[r][c]):
                # Toggle between showing user input and correct answer
                if (r, c) in self.corrected_cells:
                    # Currently showing correct answer, switch to user input
                    self.corrected_cells.remove((r, c))
                    self.grid[r][c] = self.user_input[(r, c)]
                    self.status_label.config(text=f"Showing your answer ({self.user_input[(r, c)]}) at ({r+1}, {c+1})")
                else:
                    # Currently showing user input, switch to correct answer
                    self.corrected_cells.add((r, c))
                    self.grid[r][c] = self.solution[r][c]
                    self.status_label.config(text=f"Showing correct answer ({self.solution[r][c]}) at ({r+1}, {c+1})")
                self.draw_grid()
                return
            
            # In both modes, just select the cell
            self.selected_cell = (r, c)
            self.draw_grid()
            
            if self.notes_mode:
                self.status_label.config(text=f"Selected cell ({r+1}, {c+1}) - Type numbers 1-9 to add/remove notes")
            else:
                self.status_label.config(text=f"Selected cell ({r+1}, {c+1})")
    
    def on_key_press(self, event):
        """Handle key press events"""
        if self.selected_cell is None:
            return
        
        r, c = self.selected_cell
        
        # Handle number keys 1-9
        if event.char.isdigit() and '1' <= event.char <= '9':
            num = int(event.char)
            
            if self.notes_mode:
                # In notes mode, toggle the number in notes
                if (r, c) not in self.notes:
                    self.notes[(r, c)] = set()
                
                if num in self.notes[(r, c)]:
                    self.notes[(r, c)].remove(num)
                    if not self.notes[(r, c)]:  # Remove empty set
                        del self.notes[(r, c)]
                    self.status_label.config(text=f"Removed note {num} from ({r+1}, {c+1})")
                else:
                    self.notes[(r, c)].add(num)
                    self.status_label.config(text=f"Added note {num} to ({r+1}, {c+1})")
            else:
                # Normal mode - place the number
                if self.is_valid_move(self.grid, r, c, num):
                    self.grid[r][c] = num
                    # Track user input (only for non-hint positions)
                    if (r, c) not in self.hint_positions:
                        self.user_input[(r, c)] = num
                    # Auto-remove notes when cell is filled
                    if (r, c) in self.notes:
                        del self.notes[(r, c)]
                    self.status_label.config(text=f"Placed {num} at ({r+1}, {c+1})")
                else:
                    self.status_label.config(text=f"Invalid move: {num} at ({r+1}, {c+1})")
            
            self.draw_grid()
        
        # Handle delete/backspace
        elif event.keysym in ['Delete', 'BackSpace']:
            if self.notes_mode:
                # In notes mode, clear all notes for this cell
                if (r, c) in self.notes:
                    del self.notes[(r, c)]
                    self.status_label.config(text=f"Cleared all notes from ({r+1}, {c+1})")
            else:
                # Normal mode - clear the cell
                self.grid[r][c] = 0
                # Remove from user input tracking
                if (r, c) in self.user_input:
                    del self.user_input[(r, c)]
                self.status_label.config(text=f"Cleared cell ({r+1}, {c+1})")
            self.draw_grid()
        
        # Handle arrow keys
        elif event.keysym == 'Up' and r > 0:
            self.selected_cell = (r-1, c)
            self.draw_grid()
        elif event.keysym == 'Down' and r < self.grid_size - 1:
            self.selected_cell = (r+1, c)
            self.draw_grid()
        elif event.keysym == 'Left' and c > 0:
            self.selected_cell = (r, c-1)
            self.draw_grid()
        elif event.keysym == 'Right' and c < self.grid_size - 1:
            self.selected_cell = (r, c+1)
            self.draw_grid()
    
    def check_solution(self):
        """Check if the current solution is correct"""
        # Check if all cells are filled
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if self.grid[r][c] == 0:
                    self.status_label.config(text="Please fill all cells")
                    return
        
        # Check if solution matches the correct solution
        if self.grid == self.solution:
            self.status_label.config(text="🎉 Congratulations! Solution is correct! 🎉")
            self.root.after(1500, self.show_victory_and_new_game)
        else:
            self.status_label.config(text="Solution is incorrect. Keep trying!")
    
    def show_victory_and_new_game(self):
        """Show victory message and generate new puzzle"""
        # Save the completed puzzle
        self.save_completed_puzzle()
        
        messagebox.showinfo("Sudoku", "Congratulations! You solved the puzzle! Generating new puzzle...")
        self.generate_puzzle()
        self.status_label.config(text="New puzzle generated! Click cells to select, type numbers 1-9 to fill")
    
    def get_hint(self):
        """Provide a hint by revealing one correct cell"""
        if not self.solution:
            self.status_label.config(text="No solution available")
            return
        
        # Find empty cells
        empty_cells = []
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if self.grid[r][c] == 0:
                    empty_cells.append((r, c))
        
        if not empty_cells:
            self.status_label.config(text="All cells are filled!")
            return
        
        # Choose a strategic hint position
        hint_pos = self.choose_strategic_hint(empty_cells)
        
        if hint_pos:
            r, c = hint_pos
            self.grid[r][c] = self.solution[r][c]
            self.draw_grid()
            self.status_label.config(text=f"Hint revealed at position ({r+1}, {c+1})")
        else:
            # Fallback: reveal a random empty cell
            r, c = random.choice(empty_cells)
            self.grid[r][c] = self.solution[r][c]
            self.draw_grid()
            self.status_label.config(text=f"Hint revealed at position ({r+1}, {c+1})")
    
    def choose_strategic_hint(self, empty_cells):
        """Choose a strategic position for the hint"""
        # Priority 1: Cells that would help complete a row, column, or box
        strategic_cells = []
        
        for r, c in empty_cells:
            # Count how many numbers are missing in the row
            row_numbers = set(self.grid[r])
            row_numbers.discard(0)
            row_missing = 9 - len(row_numbers)
            
            # Count how many numbers are missing in the column
            col_numbers = set(self.grid[i][c] for i in range(9))
            col_numbers.discard(0)
            col_missing = 9 - len(col_numbers)
            
            # Count how many numbers are missing in the 3x3 box
            box_row = (r // 3) * 3
            box_col = (c // 3) * 3
            box_numbers = set()
            for br in range(box_row, box_row + 3):
                for bc in range(box_col, box_col + 3):
                    if self.grid[br][bc] != 0:
                        box_numbers.add(self.grid[br][bc])
            box_missing = 9 - len(box_numbers)
            
            # Prioritize cells that would help complete rows/columns/boxes
            if row_missing <= 2 or col_missing <= 2 or box_missing <= 2:
                strategic_cells.append((r, c))
        
        if strategic_cells:
            return random.choice(strategic_cells)
        
        return None
    
    def show_solution(self):
        """Toggle between showing solution and user input"""
        # Always ensure we have a solution
        if not self.solution:
            self.status_label.config(text="Generating solution...")
            self.root.update()  # Force UI update
            
            # Create a copy of current grid and solve it
            temp_grid = [row[:] for row in self.grid]
            if self.solve_sudoku(temp_grid):
                self.solution = temp_grid
                self.status_label.config(text="Solution generated!")
            else:
                self.status_label.config(text="No solution available")
                return
        
        if self.showing_solution:
            # Currently showing solution, switch back to user input
            self.showing_solution = False
            self.restore_user_input()
            self.status_label.config(text="Showing user input")
        else:
            # Currently showing user input, switch to solution
            self.showing_solution = True
            self.show_complete_solution()
            self.status_label.config(text="Showing solution - click again to return to user input")
        
        self.draw_grid()
    
    def show_complete_solution(self):
        """Show the complete solution, highlighting incorrect user inputs"""
        # Clear corrected cells tracking
        self.corrected_cells = set()
        
        # Fill all empty cells with the correct solution
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if self.grid[r][c] == 0:
                    self.grid[r][c] = self.solution[r][c]
    
    def restore_user_input(self):
        """Restore the grid to show only user input and hints"""
        # Clear corrected cells tracking
        self.corrected_cells = set()
        
        # Reset grid to only show hints and user input
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if (r, c) not in self.hint_positions:
                    # Check if this was user input
                    if (r, c) in self.user_input:
                        self.grid[r][c] = self.user_input[(r, c)]
                    else:
                        self.grid[r][c] = 0
    
    def animate_solution(self, empty_cells):
        """Animate the solution by filling cells one by one"""
        if not empty_cells:
            # Solution complete - show completion message and auto-generate new puzzle
            self.status_label.config(text="🎉 Solution Complete! 🎉")
            self._animation_id = self.root.after(1500, self.show_completion_and_new_game)
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
        self._animation_id = self.root.after(100, lambda: self.animate_solution(empty_cells[1:]))
    
    def instant_solution(self):
        """Show the complete solution immediately without animation"""
        # Always ensure we have a solution
        if not self.solution:
            self.status_label.config(text="Generating solution...")
            self.root.update()  # Force UI update
            
            # Create a copy of current grid and solve it
            temp_grid = [row[:] for row in self.grid]
            if self.solve_sudoku(temp_grid):
                self.solution = temp_grid
            else:
                self.status_label.config(text="No solution available")
                return
        
        # Fill all empty cells immediately
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if self.grid[r][c] == 0:
                    self.grid[r][c] = self.solution[r][c]
        
        self.draw_grid()
        self.status_label.config(text="Solution displayed instantly!")
        
        # Auto-generate new puzzle after a delay
        self.root.after(2000, self.show_completion_and_new_game)
    
    def show_completion_and_new_game(self):
        """Show completion message and generate new puzzle"""
        # Save the completed puzzle
        self.save_completed_puzzle()
        
        messagebox.showinfo("Sudoku", "Congratulations! Puzzle solved! Generating new puzzle...")
        self.generate_puzzle()
        self.status_label.config(text="New puzzle generated! Click cells to select, type numbers 1-9 to fill")
    
    def save_completed_puzzle(self):
        """Save the current puzzle to completed puzzles history"""
        puzzle_data = {
            'name': f"Sudoku Puzzle {len(self.completed_puzzles) + 1}",
            'grid': [row[:] for row in self.grid],
            'solution': [row[:] for row in self.solution],
            'hint_positions': self.hint_positions.copy(),
            'notes': {pos: notes.copy() for pos, notes in self.notes.items()},
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
            text="Completed Sudoku Puzzles",
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
        
        # Start with completely empty grid
        self.grid = [[0 for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        
        # Clear notes and reset notes mode
        self.notes = {}
        self.notes_mode = False
        self.notes_btn.config(bg="#4a4a4a", text="Notes")
        self.showing_solution = False
        self.user_input = {}
        self.corrected_cells = set()
        
        # Only place the original hints (not the full solution)
        if 'hint_positions' in puzzle:
            # Use saved hint positions
            self.hint_positions = puzzle['hint_positions'].copy()
            for r, c in self.hint_positions:
                self.grid[r][c] = self.solution[r][c]
        else:
            # Fallback for old saved puzzles - reconstruct original hints
            original_hints = []
            for r in range(self.grid_size):
                for c in range(self.grid_size):
                    if puzzle['grid'][r][c] != 0:
                        original_hints.append((r, c))
            
            self.hint_positions = set(original_hints)
            for r, c in original_hints:
                self.grid[r][c] = self.solution[r][c]
        
        self.selected_cell = None
        
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
        self.status_label.config(text="New game started! Click cells to select, type numbers 1-9 to fill")
        
    def run(self):
        """Start the game"""
        self.root.mainloop()

if __name__ == "__main__":
    game = SudokuGame()
    game.run()
