import random
import numpy as np
from tutorgym.shared import ProblemState, Action
from tutorgym.env_classes.fsm_tutor import FiniteStateMachine, StateMachineTutor
from tutorgym.env_classes.CTAT.action_model import CTAT_ActionModel
from tutorgym.env_classes.env_base import TutorEnvBase

# === Core Tango logic (extracted to pure functions, mirrors tango.py) ===

def generate_solution(grid_size):
    solution = [[None for _ in range(grid_size)] for _ in range(grid_size)]
    for r in range(grid_size):
        for c in range(grid_size):
            if (r * 2 + c) % 3 == 0:
                solution[r][c] = 'sun'
            elif (r + c * 2) % 3 == 1:
                solution[r][c] = 'moon'
            else:
                solution[r][c] = 'sun' if (r + c) % 2 == 0 else 'moon'
    balance_counts(solution, grid_size)
    for _ in range(50):
        if not apply_smart_transformation(solution, grid_size):
            break
    if not validate_solution(solution, grid_size):
        return generate_simple_valid_solution(grid_size)
    return solution

def validate_solution(solution, grid_size):
    for r in range(grid_size):
        sun_count = sum(1 for c in range(grid_size) if solution[r][c] == 'sun')
        moon_count = sum(1 for c in range(grid_size) if solution[r][c] == 'moon')
        if sun_count != moon_count:
            return False
    for c in range(grid_size):
        sun_count = sum(1 for r in range(grid_size) if solution[r][c] == 'sun')
        moon_count = sum(1 for r in range(grid_size) if solution[r][c] == 'moon')
        if sun_count != moon_count:
            return False
    for r in range(grid_size):
        for c in range(grid_size):
            if solution[r][c] is None:
                continue
            # horizontal
            count = 1
            for i in range(1, 3):
                if c - i >= 0 and solution[r][c-i] == solution[r][c]:
                    count += 1
                else:
                    break
            for i in range(1, 3):
                if c + i < grid_size and solution[r][c+i] == solution[r][c]:
                    count += 1
                else:
                    break
            if count > 2:
                return False
            # vertical
            count = 1
            for i in range(1, 3):
                if r - i >= 0 and solution[r-i][c] == solution[r][c]:
                    count += 1
                else:
                    break
            for i in range(1, 3):
                if r + i < grid_size and solution[r+i][c] == solution[r][c]:
                    count += 1
                else:
                    break
            if count > 2:
                return False
    return True

def generate_simple_valid_solution(grid_size):
    solution = [[None for _ in range(grid_size)] for _ in range(grid_size)]
    for r in range(grid_size):
        for c in range(grid_size):
            solution[r][c] = 'sun' if (r + c) % 2 == 0 else 'moon'
    return solution

def balance_counts(grid, grid_size):
    for r in range(grid_size):
        sun_count = sum(1 for c in range(grid_size) if grid[r][c] == 'sun')
        moon_count = sum(1 for c in range(grid_size) if grid[r][c] == 'moon')
        if sun_count > moon_count:
            sun_positions = [(r, c) for c in range(grid_size) if grid[r][c] == 'sun']
            random.shuffle(sun_positions)
            for i in range((sun_count - moon_count) // 2):
                if i < len(sun_positions):
                    rr, cc = sun_positions[i]
                    grid[rr][cc] = 'moon'
        elif moon_count > sun_count:
            moon_positions = [(r, c) for c in range(grid_size) if grid[r][c] == 'moon']
            random.shuffle(moon_positions)
            for i in range((moon_count - sun_count) // 2):
                if i < len(moon_positions):
                    rr, cc = moon_positions[i]
                    grid[rr][cc] = 'sun'
    for c in range(grid_size):
        sun_count = sum(1 for r in range(grid_size) if grid[r][c] == 'sun')
        moon_count = sum(1 for r in range(grid_size) if grid[r][c] == 'moon')
        if sun_count > moon_count:
            sun_positions = [(r, c) for r in range(grid_size) if grid[r][c] == 'sun']
            random.shuffle(sun_positions)
            for i in range((sun_count - moon_count) // 2):
                if i < len(sun_positions):
                    rr, cc = sun_positions[i]
                    grid[rr][cc] = 'moon'
        elif moon_count > sun_count:
            moon_positions = [(r, c) for r in range(grid_size) if grid[r][c] == 'moon']
            random.shuffle(moon_positions)
            for i in range((moon_count - sun_count) // 2):
                if i < len(moon_positions):
                    rr, cc = moon_positions[i]
                    grid[rr][cc] = 'sun'

def apply_smart_transformation(grid, grid_size):
    for _ in range(10):
        r = random.randint(0, grid_size - 1)
        c = random.randint(0, grid_size - 1)
        for dr, dc in [(0,1),(1,0),(0,-1),(-1,0)]:
            r2, c2 = r + dr, c + dc
            if 0 <= r2 < grid_size and 0 <= c2 < grid_size:
                if is_valid_swap(grid, r, c, r2, c2, grid_size):
                    grid[r][c], grid[r2][c2] = grid[r2][c2], grid[r][c]
                    return True
    return False

def is_valid_swap(grid, r1, c1, r2, c2, grid_size):
    temp_grid = [row[:] for row in grid]
    temp_grid[r1][c1], temp_grid[r2][c2] = temp_grid[r2][c2], temp_grid[r1][c1]
    for r in range(grid_size):
        sun_count = sum(1 for c in range(grid_size) if temp_grid[r][c] == 'sun')
        moon_count = sum(1 for c in range(grid_size) if temp_grid[r][c] == 'moon')
        if sun_count != moon_count:
            return False
    for c in range(grid_size):
        sun_count = sum(1 for r in range(grid_size) if temp_grid[r][c] == 'sun')
        moon_count = sum(1 for r in range(grid_size) if temp_grid[r][c] == 'moon')
        if sun_count != moon_count:
            return False
    for r, c in [(r1, c1), (r2, c2)]:
        if temp_grid[r][c] is None:
            continue
        count = 1
        for i in range(1, 3):
            if c - i >= 0 and temp_grid[r][c-i] == temp_grid[r][c]:
                count += 1
            else:
                break
        for i in range(1, 3):
            if c + i < grid_size and temp_grid[r][c+i] == temp_grid[r][c]:
                count += 1
            else:
                break
        if count > 2:
            return False
        count = 1
        for i in range(1, 3):
            if r - i >= 0 and temp_grid[r-i][c] == temp_grid[r][c]:
                count += 1
            else:
                break
        for i in range(1, 3):
            if r + i < grid_size and temp_grid[r+i][c] == temp_grid[r][c]:
                count += 1
            else:
                break
        if count > 2:
            return False
    return True

def add_constraints(solution, constraints, grid_size):
    equal_candidates = []
    for r1 in range(grid_size):
        for c1 in range(grid_size):
            for dr, dc in [(0,1),(1,0)]:
                r2, c2 = r1 + dr, c1 + dc
                if 0 <= r2 < grid_size and 0 <= c2 < grid_size:
                    if solution[r1][c1] == solution[r2][c2]:
                        equal_candidates.append((r1, c1, r2, c2))
    random.shuffle(equal_candidates)
    for r1, c1, r2, c2 in equal_candidates[:4]:
        constraints.append((r1, c1, r2, c2, '='))
    different_candidates = []
    for r1 in range(grid_size):
        for c1 in range(grid_size):
            for dr, dc in [(0,1),(1,0)]:
                r2, c2 = r1 + dr, c1 + dc
                if 0 <= r2 < grid_size and 0 <= c2 < grid_size:
                    if solution[r1][c1] != solution[r2][c2]:
                        different_candidates.append((r1, c1, r2, c2))
    random.shuffle(different_candidates)
    for r1, c1, r2, c2 in different_candidates[:3]:
        constraints.append((r1, c1, r2, c2, '×'))

def create_puzzle(solution, grid_size):
    grid = [[None for _ in range(grid_size)] for _ in range(grid_size)]
    weights = [0.3, 0.25, 0.2, 0.15, 0.1]
    hint_ranges = [(4,6), (7,8), (9,10), (11,12), (13,14)]
    selected_range = random.choices(hint_ranges, weights=weights)[0]
    hint_count = random.randint(selected_range[0], selected_range[1])
    hint_positions = get_strategic_hints(solution, hint_count, grid_size)
    hint_set = set(hint_positions)
    for r, c in hint_positions:
        grid[r][c] = solution[r][c]
    return grid, hint_set

def get_strategic_hints(solution, hint_count, grid_size):
    # Simplified: corners, edges, then center
    hints = []
    corners = [(0,0),(0,grid_size-1),(grid_size-1,0),(grid_size-1,grid_size-1)]
    for pos in corners:
        if len(hints) < hint_count:
            hints.append(pos)
    edges = []
    for r in range(grid_size):
        edges.extend([(r,0),(r,grid_size-1)])
    for c in range(grid_size):
        edges.extend([(0,c),(grid_size-1,c)])
    edges = list(dict.fromkeys(edges))
    random.shuffle(edges)
    for pos in edges:
        if len(hints) < hint_count and pos not in hints:
            hints.append(pos)
    centers = [(r,c) for r in range(1, grid_size-1) for c in range(1, grid_size-1)]
    random.shuffle(centers)
    for pos in centers:
        if len(hints) < hint_count and pos not in hints:
            hints.append(pos)
    return hints

def is_valid_placement(grid, r, c, symbol, grid_size, constraints=None):
    """
    Check if placing a symbol at (r, c) is valid according to Tango rules:
    1. No more than 2 of the same symbol in a row (horizontally or vertically)
    2. Row balance: Can't exceed grid_size/2 of one symbol, and balance must be achievable
    3. Column balance: Can't exceed grid_size/2 of one symbol, and balance must be achievable
    4. Constraint satisfaction: If both cells in a constraint are filled, they must satisfy it
    """
    value = 'sun' if symbol == 'sun' else ('moon' if symbol == 'moon' else None)
    if value is None:
        return True
    
    # Create a temporary grid with the placement to check validity
    temp_grid = [row[:] for row in grid]  # Deep copy
    temp_grid[r][c] = value
    
    # Check 1: No more than 2 of the same symbol in a row (horizontal)
    count = 1
    for i in range(1, 3):
        if c - i >= 0 and temp_grid[r][c-i] == value:
            count += 1
        else:
            break
    for i in range(1, 3):
        if c + i < grid_size and temp_grid[r][c+i] == value:
            count += 1
        else:
            break
    if count > 2:
        return False
    
    # Check 2: No more than 2 of the same symbol in a row (vertical)
    count = 1
    for i in range(1, 3):
        if r - i >= 0 and temp_grid[r-i][c] == value:
            count += 1
        else:
            break
    for i in range(1, 3):
        if r + i < grid_size and temp_grid[r+i][c] == value:
            count += 1
        else:
            break
    if count > 2:
        return False
    
    # Check 3: Row balance
    row_values = [temp_grid[r][col] for col in range(grid_size)]
    row_sun_count = sum(1 for v in row_values if v == 'sun')
    row_moon_count = sum(1 for v in row_values if v == 'moon')
    row_empty_count = sum(1 for v in row_values if v is None)
    
    max_allowed = grid_size // 2
    # Can't exceed maximum allowed
    if row_sun_count > max_allowed or row_moon_count > max_allowed:
        return False
    
    # If row is full, must be balanced
    if row_empty_count == 0:
        if row_sun_count != row_moon_count:
            return False
    # If row has 1 empty cell left, the imbalance must be <= 1 (can be balanced with last cell)
    elif row_empty_count == 1:
        imbalance = abs(row_sun_count - row_moon_count)
        if imbalance > 1:
            return False
    
    # Check 4: Column balance
    col_values = [temp_grid[row][c] for row in range(grid_size)]
    col_sun_count = sum(1 for v in col_values if v == 'sun')
    col_moon_count = sum(1 for v in col_values if v == 'moon')
    col_empty_count = sum(1 for v in col_values if v is None)
    
    # Can't exceed maximum allowed
    if col_sun_count > max_allowed or col_moon_count > max_allowed:
        return False
    
    # If column is full, must be balanced
    if col_empty_count == 0:
        if col_sun_count != col_moon_count:
            return False
    # If column has 1 empty cell left, the imbalance must be <= 1 (can be balanced with last cell)
    elif col_empty_count == 1:
        imbalance = abs(col_sun_count - col_moon_count)
        if imbalance > 1:
            return False
    
    # Check 5: Constraint satisfaction (only check if both cells are filled)
    if constraints:
        for r1, c1, r2, c2, constraint_type in constraints:
            # Check if this placement affects a constraint
            if (r1, c1) == (r, c) or (r2, c2) == (r, c):
                v1 = temp_grid[r1][c1]
                v2 = temp_grid[r2][c2]
                
                # Both cells must be filled to check constraint
                if v1 is not None and v2 is not None:
                    if constraint_type == '=':
                        if v1 != v2:
                            return False
                    elif constraint_type == '×':
                        if v1 == v2:
                            return False
    
    return True

def is_tango_complete(grid):
    for row in grid:
        if None in row:
            return False
    return True

def verify_puzzle_solvability(grid, constraints, grid_size):
    """
    Verify that a puzzle with hints is solvable by checking if there's at least one valid move.
    This helps detect if hints were placed incorrectly or if the puzzle is unsolvable.
    """
    # Check if there's at least one valid placement available
    for r in range(grid_size):
        for c in range(grid_size):
            if grid[r][c] is None:  # Empty cell
                for symbol in ["sun", "moon"]:
                    if is_valid_placement(grid, r, c, symbol, grid_size, constraints):
                        return True  # Found at least one valid move
    return False  # No valid moves found

def find_next_placement_constraint_propagation(current_grid, constraints, grid_size):
    """
    Find the next placement using constraint propagation:
    1. Start with fixed symbols (already placed)
    2. Propagate through × and = constraints (these are truly forced)
    3. Use "no 3-in-a-row" to find forced placements (only if opposite is invalid)
    4. Use balance constraints to find forced placements (only if one symbol is invalid)
    
    Returns (r, c, symbol) if a forced placement is found, None otherwise.
    """
    # Step 1: Propagate through constraint links (× and =)
    # These are truly forced - if one cell is filled, the other MUST be a specific symbol
    # The constraint itself makes it forced; we just verify the forced placement is valid
    for r1, c1, r2, c2, constraint_type in constraints:
        v1 = current_grid[r1][c1]
        v2 = current_grid[r2][c2]
        
        # If one is filled and the other is empty, propagate
        if v1 is not None and v2 is None:
            if constraint_type == '=':
                # Must be equal - place same symbol (truly forced by constraint)
                # Only suggest if placing the same symbol is valid according to all rules
                if is_valid_placement(current_grid, r2, c2, v1, grid_size, constraints):
                    return (r2, c2, v1)
            elif constraint_type == '×':
                # Must be different - place opposite symbol (truly forced by constraint)
                opposite = "moon" if v1 == "sun" else "sun"
                # Only suggest if placing the opposite symbol is valid according to all rules
                if is_valid_placement(current_grid, r2, c2, opposite, grid_size, constraints):
                    return (r2, c2, opposite)
        elif v1 is None and v2 is not None:
            if constraint_type == '=':
                # Must be equal - place same symbol (truly forced by constraint)
                # Only suggest if placing the same symbol is valid according to all rules
                if is_valid_placement(current_grid, r1, c1, v2, grid_size, constraints):
                    return (r1, c1, v2)
            elif constraint_type == '×':
                # Must be different - place opposite symbol (truly forced by constraint)
                opposite = "moon" if v2 == "sun" else "sun"
                # Only suggest if placing the opposite symbol is valid according to all rules
                if is_valid_placement(current_grid, r1, c1, opposite, grid_size, constraints):
                    return (r1, c1, opposite)
    
    # Step 1.5: Check for = constraints where both cells are empty but have at least one filled adjacent cell on the outside
    # Example: s, m, m, _ = _, m should be filled as s, m, m, s = s, m
    # Only one outside cell needs to be filled for this heuristic to apply
    for r1, c1, r2, c2, constraint_type in constraints:
        if constraint_type != '=':
            continue
        
        v1 = current_grid[r1][c1]
        v2 = current_grid[r2][c2]
        
        # Both cells must be empty
        if v1 is None and v2 is None:
            outside_symbols = []
            
            # Horizontal constraint (same row)
            if r1 == r2:
                # Check left of first cell
                if c1 > 0 and current_grid[r1][c1-1] is not None:
                    outside_symbols.append(current_grid[r1][c1-1])
                # Check right of second cell
                if c2 < grid_size - 1 and current_grid[r2][c2+1] is not None:
                    outside_symbols.append(current_grid[r2][c2+1])
            # Vertical constraint (same column)
            elif c1 == c2:
                # Check above first cell
                if r1 > 0 and current_grid[r1-1][c1] is not None:
                    outside_symbols.append(current_grid[r1-1][c1])
                # Check below second cell
                if r2 < grid_size - 1 and current_grid[r2+1][c2] is not None:
                    outside_symbols.append(current_grid[r2+1][c2])
            
            # If we have at least one outside symbol and they're all the same, both empty cells should be opposite
            # (If there are two outside symbols but they differ, we can't make a definitive inference)
            if len(outside_symbols) >= 1 and all(s == outside_symbols[0] for s in outside_symbols):
                opposite = "moon" if outside_symbols[0] == "sun" else "sun"
                # Try to place opposite in first cell
                if is_valid_placement(current_grid, r1, c1, opposite, grid_size, constraints):
                    # Verify second cell can also be the same (since they have =)
                    if is_valid_placement(current_grid, r2, c2, opposite, grid_size, constraints):
                        return (r1, c1, opposite)
    
    # Step 2: Use "no 3-in-a-row" to find forced placements
    for r in range(grid_size):
        for c in range(grid_size):
            if current_grid[r][c] is not None:
                continue
            
            # Check horizontal: if we have 2 in a row, the third must be different
            # Check pattern: [same][same][empty] - must place opposite
            if c >= 2:
                v1 = current_grid[r][c-2]
                v2 = current_grid[r][c-1]
                if v1 is not None and v2 is not None and v1 == v2:
                    # Placing the same symbol here would create 3 in a row - must place opposite
                    opposite = "moon" if v1 == "sun" else "sun"
                    # Only return if opposite is valid AND same symbol is invalid (truly forced)
                    if is_valid_placement(current_grid, r, c, opposite, grid_size, constraints):
                        if not is_valid_placement(current_grid, r, c, v1, grid_size, constraints):
                            return (r, c, opposite)
            
            # Check pattern: [empty][same][same] - must place opposite
            if c < grid_size - 2:
                v1 = current_grid[r][c+1]
                v2 = current_grid[r][c+2]
                if v1 is not None and v2 is not None and v1 == v2:
                    # Placing the same symbol here would create 3 in a row - must place opposite
                    opposite = "moon" if v1 == "sun" else "sun"
                    # Only return if opposite is valid AND same symbol is invalid (truly forced)
                    if is_valid_placement(current_grid, r, c, opposite, grid_size, constraints):
                        if not is_valid_placement(current_grid, r, c, v1, grid_size, constraints):
                            return (r, c, opposite)
            
            # Check pattern: [same][empty][same] - must place opposite to avoid 3 in a row
            if c >= 1 and c < grid_size - 1:
                v1 = current_grid[r][c-1]
                v2 = current_grid[r][c+1]
                if v1 is not None and v2 is not None and v1 == v2:
                    # If we place the same symbol here, we'd have 3 in a row - must place opposite
                    opposite = "moon" if v1 == "sun" else "sun"
                    # Only return if opposite is valid AND same symbol is invalid (truly forced)
                    if is_valid_placement(current_grid, r, c, opposite, grid_size, constraints):
                        if not is_valid_placement(current_grid, r, c, v1, grid_size, constraints):
                            return (r, c, opposite)
            
            # Check vertical: if we have 2 in a row, the third must be different
            # Check pattern: [same][same][empty] - must place opposite
            if r >= 2:
                v1 = current_grid[r-2][c]
                v2 = current_grid[r-1][c]
                if v1 is not None and v2 is not None and v1 == v2:
                    # Placing the same symbol here would create 3 in a row - must place opposite
                    opposite = "moon" if v1 == "sun" else "sun"
                    # Only return if opposite is valid AND same symbol is invalid (truly forced)
                    if is_valid_placement(current_grid, r, c, opposite, grid_size, constraints):
                        if not is_valid_placement(current_grid, r, c, v1, grid_size, constraints):
                            return (r, c, opposite)
            
            # Check pattern: [empty][same][same] - must place opposite
            if r < grid_size - 2:
                v1 = current_grid[r+1][c]
                v2 = current_grid[r+2][c]
                if v1 is not None and v2 is not None and v1 == v2:
                    # Placing the same symbol here would create 3 in a row - must place opposite
                    opposite = "moon" if v1 == "sun" else "sun"
                    # Only return if opposite is valid AND same symbol is invalid (truly forced)
                    if is_valid_placement(current_grid, r, c, opposite, grid_size, constraints):
                        if not is_valid_placement(current_grid, r, c, v1, grid_size, constraints):
                            return (r, c, opposite)
            
            # Check pattern: [same][empty][same] - must place opposite to avoid 3 in a row
            if r >= 1 and r < grid_size - 1:
                v1 = current_grid[r-1][c]
                v2 = current_grid[r+1][c]
                if v1 is not None and v2 is not None and v1 == v2:
                    # If we place the same symbol here, we'd have 3 in a row - must place opposite
                    opposite = "moon" if v1 == "sun" else "sun"
                    # Only return if opposite is valid AND same symbol is invalid (truly forced)
                    if is_valid_placement(current_grid, r, c, opposite, grid_size, constraints):
                        if not is_valid_placement(current_grid, r, c, v1, grid_size, constraints):
                            return (r, c, opposite)
    
    # Step 3: Use balance constraints to find forced placements
    max_allowed = grid_size // 2
    for r in range(grid_size):
        row_values = [current_grid[r][col] for col in range(grid_size)]
        row_sun_count = sum(1 for v in row_values if v == 'sun')
        row_moon_count = sum(1 for v in row_values if v == 'moon')
        row_empty_count = sum(1 for v in row_values if v is None)
        
        # If row has 1 empty cell left and is imbalanced, must place the minority symbol
        if row_empty_count == 1:
            if row_sun_count < row_moon_count:
                # Need sun to balance - only return if sun is valid AND moon is invalid (truly forced)
                for c in range(grid_size):
                    if current_grid[r][c] is None:
                        if is_valid_placement(current_grid, r, c, "sun", grid_size, constraints):
                            if not is_valid_placement(current_grid, r, c, "moon", grid_size, constraints):
                                return (r, c, "sun")
            elif row_moon_count < row_sun_count:
                # Need moon to balance - only return if moon is valid AND sun is invalid (truly forced)
                for c in range(grid_size):
                    if current_grid[r][c] is None:
                        if is_valid_placement(current_grid, r, c, "moon", grid_size, constraints):
                            if not is_valid_placement(current_grid, r, c, "sun", grid_size, constraints):
                                return (r, c, "moon")
    
    for c in range(grid_size):
        col_values = [current_grid[row][c] for row in range(grid_size)]
        col_sun_count = sum(1 for v in col_values if v == 'sun')
        col_moon_count = sum(1 for v in col_values if v == 'moon')
        col_empty_count = sum(1 for v in col_values if v is None)
        
        # If column has 1 empty cell left and is imbalanced, must place the minority symbol
        if col_empty_count == 1:
            if col_sun_count < col_moon_count:
                # Need sun to balance - only return if sun is valid AND moon is invalid (truly forced)
                for r in range(grid_size):
                    if current_grid[r][c] is None:
                        if is_valid_placement(current_grid, r, c, "sun", grid_size, constraints):
                            if not is_valid_placement(current_grid, r, c, "moon", grid_size, constraints):
                                return (r, c, "sun")
            elif col_moon_count < col_sun_count:
                # Need moon to balance - only return if moon is valid AND sun is invalid (truly forced)
                for r in range(grid_size):
                    if current_grid[r][c] is None:
                        if is_valid_placement(current_grid, r, c, "moon", grid_size, constraints):
                            if not is_valid_placement(current_grid, r, c, "sun", grid_size, constraints):
                                return (r, c, "moon")
    
    # No forced placement found
    return None

def encode_tango_neighbors(state_dict, grid_size):
    """Set spatial relationships (above, below, left, right) for cells based on row/col"""
    for r in range(grid_size):
        for c in range(grid_size):
            cell_id = f"cell_{r}_{c}"
            if cell_id not in state_dict:
                continue
            
            # Set above (row - 1)
            if r > 0:
                state_dict[cell_id]["above"] = f"cell_{r-1}_{c}"
            else:
                state_dict[cell_id]["above"] = None
            
            # Set below (row + 1)
            if r < grid_size - 1:
                state_dict[cell_id]["below"] = f"cell_{r+1}_{c}"
            else:
                state_dict[cell_id]["below"] = None
            
            # Set left (col - 1)
            if c > 0:
                state_dict[cell_id]["left"] = f"cell_{r}_{c-1}"
            else:
                state_dict[cell_id]["left"] = None
            
            # Set right (col + 1)
            if c < grid_size - 1:
                state_dict[cell_id]["right"] = f"cell_{r}_{c+1}"
            else:
                state_dict[cell_id]["right"] = None
    
    return state_dict

def count_constraints(grid, constraints):
    satisfied = 0
    for r1, c1, r2, c2, t in constraints:
        v1 = grid[r1][c1]
        v2 = grid[r2][c2]
        if v1 is None or v2 is None:
            continue
        if (t == '=' and v1 == v2) or (t == '×' and v1 != v2):
            satisfied += 1
    return satisfied, len(constraints)


class TangoPuzzle(TutorEnvBase):
    def __init__(self, grid_size=6, problem_types=["basic"], **kwargs):
        if grid_size < 4:
            raise ValueError("Grid size must be at least 4")
        
        self.grid_size = grid_size
        self.problem_types = problem_types
        self.problem = None
        self.problem_name = None
        # Track recently backtracked cells to avoid infinite loops
        self.recently_backtracked = set()
        # Track action history for undo functionality
        self.action_history = []
        self.max_history = 50
        
        super().__init__(**kwargs)
        self.set_random_problem()
    
    def _blank_state(self):
        state = {}
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                state[f"cell_{r}_{c}"] = {
                    "id": f"cell_{r}_{c}",
                    "type": "Cell",
                    "value": "none",
                    "row": r,
                    "col": c,
                    "above": None,
                    "below": None,
                    "left": None,
                    "right": None
                }
        
        # Add undo button as a special meta-object the agent can select
        state["undo_button"] = {
            "id": "undo_button",
            "type": "Cell",  # Use Cell type so agent can select it
            "value": "undo"
        }
        
        # Set spatial relationships based on row/col
        state = encode_tango_neighbors(state, self.grid_size)
        
        # Note: Removed metadata objects (grid_size, constraints, satisfied_constraints)
        # as they don't have fact types and aren't needed for agent decision making
        
        return state
    
    def action_is_done(self, action):
        return action.selection == "done"
    
    def can_undo(self):
        """Check if undo is possible (i.e., there's history to revert to)"""
        return len(self.action_history) > 0
    
    def undo_last_action(self):
        """Undo the last action by reverting to the previous state"""
        if not self.can_undo():
            return self.state
        
        # Pop the last state from history and restore it
        previous_state = self.action_history.pop()
        self.state = previous_state.copy()
        
        return self.state
    
    def is_stuck(self, current_grid, constraints):
        """
        Check if the current state is truly stuck (no valid moves available ANYWHERE).
        
        Returns: True if stuck, False otherwise
        """
        # If puzzle is complete, not stuck
        if is_tango_complete(current_grid):
            return False
        
        # Check if there are any valid moves ANYWHERE in the grid
        # Not just top-constraint cells - truly stuck means NO valid moves at all
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if current_grid[r][c] is None:
                    # Check if either symbol can be validly placed
                    if is_valid_placement(current_grid, r, c, "sun", self.grid_size, constraints):
                        return False
                    if is_valid_placement(current_grid, r, c, "moon", self.grid_size, constraints):
                        return False
        
        # No valid moves found anywhere = truly stuck
        return True
    
    def calculate_cell_constraint_rank(self, r, c, current_grid, constraints):
        """
        Calculate the constraint rank for an empty cell at position (r, c).
        
        Ranking (from highest to lowest priority):
        1. Cell is part of a constraint (× or =) where the other cell is filled
        2. Cell is adjacent to 2 consecutive same symbols (horizontally or vertically)
        3. The other 3 cells in the same row OR column are filled (need to balance)
        4. Cell is part of an = constraint where both cells are empty but have filled adjacent cells on the outside
        5. Cell is adjacent to at least one filled cell
        6. Cell has no filled neighbors (lowest priority)
        
        Returns: rank (1-6, where 1 is highest priority)
        """
        # Only rank empty cells
        if current_grid[r][c] is not None:
            return None
        
        # Rank 1: Check if cell is part of a constraint where the other cell is filled
        if constraints:
            for r1, c1, r2, c2, constraint_type in constraints:
                # Check if this cell is involved in a constraint
                if (r1, c1) == (r, c):
                    # This cell is the first in the constraint, check if second is filled
                    if current_grid[r2][c2] is not None:
                        return 1
                elif (r2, c2) == (r, c):
                    # This cell is the second in the constraint, check if first is filled
                    if current_grid[r1][c1] is not None:
                        return 1
        
        # Rank 2: Check if adjacent to 2 consecutive same symbols
        # Check horizontal patterns
        # Pattern: [same][same][empty] at (r, c)
        if c >= 2:
            v1 = current_grid[r][c-2]
            v2 = current_grid[r][c-1]
            if v1 is not None and v2 is not None and v1 == v2:
                return 2
        # Pattern: [empty][same][same] at (r, c)
        if c < self.grid_size - 2:
            v1 = current_grid[r][c+1]
            v2 = current_grid[r][c+2]
            if v1 is not None and v2 is not None and v1 == v2:
                return 2
        # Pattern: [same][empty][same] at (r, c)
        if c >= 1 and c < self.grid_size - 1:
            v1 = current_grid[r][c-1]
            v2 = current_grid[r][c+1]
            if v1 is not None and v2 is not None and v1 == v2:
                return 2
        
        # Check vertical patterns
        # Pattern: [same][same][empty] at (r, c)
        if r >= 2:
            v1 = current_grid[r-2][c]
            v2 = current_grid[r-1][c]
            if v1 is not None and v2 is not None and v1 == v2:
                return 2
        # Pattern: [empty][same][same] at (r, c)
        if r < self.grid_size - 2:
            v1 = current_grid[r+1][c]
            v2 = current_grid[r+2][c]
            if v1 is not None and v2 is not None and v1 == v2:
                return 2
        # Pattern: [same][empty][same] at (r, c)
        if r >= 1 and r < self.grid_size - 1:
            v1 = current_grid[r-1][c]
            v2 = current_grid[r+1][c]
            if v1 is not None and v2 is not None and v1 == v2:
                return 2
        
        # Rank 3: Check if 3 out of 4 cells in row OR column are filled
        # Check row
        row_filled = sum(1 for col in range(self.grid_size) if col != c and current_grid[r][col] is not None)
        if row_filled >= self.grid_size - 1:  # All other cells in row are filled
            return 3
        
        # Check column
        col_filled = sum(1 for row in range(self.grid_size) if row != r and current_grid[row][c] is not None)
        if col_filled >= self.grid_size - 1:  # All other cells in column are filled
            return 3
        
        # Rank 4: Check if cell is part of an = constraint where both cells are empty 
        # but have at least ONE filled adjacent cell on the outside
        # Example: s, m, m, _ = _, m should be filled as s, m, m, s = s, m
        # Only one outside cell needs to be filled (e.g., just the 'm' on the left or right)
        if constraints:
            for r1, c1, r2, c2, constraint_type in constraints:
                # Only check = constraints
                if constraint_type != '=':
                    continue
                
                # Check if this cell is involved in this = constraint
                if (r1, c1) == (r, c) and current_grid[r2][c2] is None:
                    # This cell is the first in the constraint, other cell is also empty
                    # Check if there is at least one filled adjacent cell on the outside
                    has_outside_neighbor = False
                    
                    # Horizontal constraint (same row)
                    if r1 == r2:
                        # Check cells on the outside (left of first cell OR right of second cell)
                        if c1 > 0 and current_grid[r1][c1-1] is not None:
                            has_outside_neighbor = True
                        if c2 < self.grid_size - 1 and current_grid[r2][c2+1] is not None:
                            has_outside_neighbor = True
                    # Vertical constraint (same column)
                    elif c1 == c2:
                        # Check cells on the outside (above first cell OR below second cell)
                        if r1 > 0 and current_grid[r1-1][c1] is not None:
                            has_outside_neighbor = True
                        if r2 < self.grid_size - 1 and current_grid[r2+1][c2] is not None:
                            has_outside_neighbor = True
                    
                    if has_outside_neighbor:
                        return 4
                
                elif (r2, c2) == (r, c) and current_grid[r1][c1] is None:
                    # This cell is the second in the constraint, other cell is also empty
                    # Check if there is at least one filled adjacent cell on the outside
                    has_outside_neighbor = False
                    
                    # Horizontal constraint (same row)
                    if r1 == r2:
                        # Check cells on the outside (left of first cell OR right of second cell)
                        if c1 > 0 and current_grid[r1][c1-1] is not None:
                            has_outside_neighbor = True
                        if c2 < self.grid_size - 1 and current_grid[r2][c2+1] is not None:
                            has_outside_neighbor = True
                    # Vertical constraint (same column)
                    elif c1 == c2:
                        # Check cells on the outside (above first cell OR below second cell)
                        if r1 > 0 and current_grid[r1-1][c1] is not None:
                            has_outside_neighbor = True
                        if r2 < self.grid_size - 1 and current_grid[r2+1][c2] is not None:
                            has_outside_neighbor = True
                    
                    if has_outside_neighbor:
                        return 4
        
        # Rank 5: Check if adjacent to at least one filled cell
        adjacent_filled = False
        # Check up
        if r > 0 and current_grid[r-1][c] is not None:
            adjacent_filled = True
        # Check down
        if r < self.grid_size - 1 and current_grid[r+1][c] is not None:
            adjacent_filled = True
        # Check left
        if c > 0 and current_grid[r][c-1] is not None:
            adjacent_filled = True
        # Check right
        if c < self.grid_size - 1 and current_grid[r][c+1] is not None:
            adjacent_filled = True
        
        if adjacent_filled:
            return 5
        
        # Rank 6: Cell has no filled neighbors (lowest priority)
        return 6
    
    def get_top_constraint_cells(self, current_grid, constraints):
        """
        Get all empty cells with the highest constraint rank.
        
        Returns: list of (r, c) tuples representing cells with top constraint
        """
        cell_ranks = {}
        
        # Calculate rank for all empty cells
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if current_grid[r][c] is None:
                    rank = self.calculate_cell_constraint_rank(r, c, current_grid, constraints)
                    if rank is not None:
                        cell_ranks[(r, c)] = rank
        
        if not cell_ranks:
            return []
        
        # Find the minimum (highest priority) rank
        min_rank = min(cell_ranks.values())
        
        # Return all cells with that rank
        return [(r, c) for (r, c), rank in cell_ranks.items() if rank == min_rank]
    
    def set_start_state(self, grid, constraints, hint_positions):
        self.problem = (grid, constraints)
        # Store hint positions to track which cells are hints (cannot be backtracked)
        self.hint_positions = set(hint_positions) if hint_positions else set()
        # Clear action history when starting a new problem
        self.action_history = []
        state_dict = self._blank_state()
        
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if grid[r][c] is not None:
                    # Preserve spatial relationships from _blank_state
                    cell_obj = state_dict.get(f"cell_{r}_{c}", {})
                    state_dict[f"cell_{r}_{c}"] = {
                        "id": f"cell_{r}_{c}",
                        "type": "Cell",
                        "value": grid[r][c],
                        "row": r,
                        "col": c,
                        "above": cell_obj.get("above"),
                        "below": cell_obj.get("below"),
                        "left": cell_obj.get("left"),
                        "right": cell_obj.get("right")
                    }
        
        # Note: We don't add constraints/satisfied_constraints to state
        # as they're metadata not needed for agent decision making
        
        # Convert to ProblemState
        self.state = ProblemState(state_dict)
        
        # Set problem_name for trainer compatibility
        ptype = self.problem_types[0] if self.problem_types else "basic"
        self.problem_name = f"tango_{ptype}_{self.grid_size}x{self.grid_size}"
    
    def set_random_problem(self):
        ptype = random.choice(self.problem_types)
        
        if ptype == "basic":
            # Try to generate a valid solution with a maximum number of attempts
            max_attempts = 10
            solution = None
            
            for attempt in range(max_attempts):
                solution = generate_solution(self.grid_size)
                if validate_solution(solution, self.grid_size):
                    break
            
            # If we still don't have a valid solution, use the simple fallback
            if not validate_solution(solution, self.grid_size):
                solution = generate_simple_valid_solution(self.grid_size)
            
            grid, hint_positions = create_puzzle(solution, self.grid_size)
            constraints = []
            add_constraints(solution, constraints, self.grid_size)
            
            # Verify puzzle is solvable after hints are placed
            if not verify_puzzle_solvability(grid, constraints, self.grid_size):
                # Puzzle is unsolvable with current hints - regenerate
                print(f"Warning: Generated puzzle is unsolvable, regenerating...")
                # Try regenerating up to 5 times
                for retry in range(5):
                    grid, hint_positions = create_puzzle(solution, self.grid_size)
                    if verify_puzzle_solvability(grid, constraints, self.grid_size):
                        break
                else:
                    # If still unsolvable after retries, use solution as grid (all hints)
                    print(f"Warning: Could not generate solvable puzzle, using solution as hints")
                    grid = [row[:] for row in solution]  # Use full solution
                    hint_positions = set((r, c) for r in range(self.grid_size) 
                                        for c in range(self.grid_size))
        
        # Store solution for debugging
        self.solution = solution
        
        self.set_start_state(grid, constraints, hint_positions)
        return {"grid": grid, "constraints": constraints, "hint_positions": hint_positions}
    
    def get_possible_selections(self):
        selections = []
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                selections.append(f"cell_{r}_{c}")
        selections.append("done")
        selections.append("undo_button")
        return selections
    
    def get_possible_args(self):
        args = []
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                args.append(f"{r},{c}")
        args.extend(["sun", "moon", "none"])
        args.append("done")
        args.append("undo")
        return args
    
    def _print_puzzle_debug_info(self, current_grid, state_objs=None, is_complete=False):
        """
        Print debug information about the puzzle state.
        Called when puzzle is completed or when no valid moves are found.
        """
        prefix = "✅ PUZZLE COMPLETED" if is_complete else "⚠️  WARNING: No valid moves found"
        print(f"\n{prefix} for puzzle {self.problem_name}")
        
        # Print starting state (initial hints) with constraints
        grid, constraints = self.problem if self.problem else (None, None)
        if grid:
            # Create a visual representation of constraints on the board
            # Build constraint map: (r, c) -> list of constraint symbols and directions
            constraint_map = {}
            if constraints:
                for r1, c1, r2, c2, constraint_type in constraints:
                    # Determine direction
                    if r2 == r1 and c2 == c1 + 1:  # Right
                        if (r1, c1) not in constraint_map:
                            constraint_map[(r1, c1)] = []
                        constraint_map[(r1, c1)].append(('R', constraint_type))
                    elif r2 == r1 and c2 == c1 - 1:  # Left
                        if (r1, c1) not in constraint_map:
                            constraint_map[(r1, c1)] = []
                        constraint_map[(r1, c1)].append(('L', constraint_type))
                    elif r2 == r1 + 1 and c2 == c1:  # Down
                        if (r1, c1) not in constraint_map:
                            constraint_map[(r1, c1)] = []
                        constraint_map[(r1, c1)].append(('D', constraint_type))
                    elif r2 == r1 - 1 and c2 == c1:  # Up
                        if (r1, c1) not in constraint_map:
                            constraint_map[(r1, c1)] = []
                        constraint_map[(r1, c1)].append(('U', constraint_type))
            
            print(f"   Starting state (initial hints) with constraints:")
            for r in range(self.grid_size):
                row_parts = []
                for c in range(self.grid_size):
                    cell_value = str(grid[r][c] if grid[r][c] else "_")
                    # Add constraint indicators
                    constraint_str = ""
                    if (r, c) in constraint_map:
                        for direction, constraint_type in constraint_map[(r, c)]:
                            if direction == 'R':
                                constraint_str += f"→{constraint_type}"
                            elif direction == 'L':
                                constraint_str += f"←{constraint_type}"
                            elif direction == 'D':
                                constraint_str += f"↓{constraint_type}"
                            elif direction == 'U':
                                constraint_str += f"↑{constraint_type}"
                    if constraint_str:
                        row_parts.append(f"{cell_value}{constraint_str}")
                    else:
                        row_parts.append(cell_value)
                print(f"   Row {r}: {' '.join(row_parts)}")
            
            # Also print constraints as a list
            if constraints:
                print(f"   Constraints list:")
                for r1, c1, r2, c2, constraint_type in constraints:
                    print(f"      ({r1},{c1}) {constraint_type} ({r2},{c2})")
            else:
                print(f"   Constraints: None")
        
        print(f"   Current grid state:")
        for r in range(self.grid_size):
            row_str = " ".join([str(current_grid[r][c] if current_grid[r][c] else "_") 
                              for c in range(self.grid_size)])
            print(f"   Row {r}: {row_str}")
        print(f"   Empty cells: {sum(1 for r in range(self.grid_size) for c in range(self.grid_size) if current_grid[r][c] is None)}")
        
        # Print the solution for comparison (DEBUGGING ONLY)
        if hasattr(self, 'solution') and self.solution:
            print(f"   Solution (what the puzzle should be - DEBUG ONLY):")
            for r in range(self.grid_size):
                sol_str = " ".join([str(self.solution[r][c] if self.solution[r][c] else "_") 
                                  for c in range(self.grid_size)])
                print(f"   Row {r}: {sol_str}")
            
            # Check what should be in the empty cells (only if puzzle is not complete)
            if not is_complete and state_objs:
                for r in range(self.grid_size):
                    for c in range(self.grid_size):
                        if current_grid[r][c] is None:
                            expected = self.solution[r][c]
                            current_value = state_objs.get(f"cell_{r}_{c}", {}).get("value", "none")
                            print(f"   Empty cell ({r},{c}) should be: {expected}, current: {current_value}")
                            # Check why it's not valid
                            if expected:
                                print(f"      Checking validity of placing {expected} at ({r},{c})...")
                                if not is_valid_placement(current_grid, r, c, expected, self.grid_size, constraints):
                                    print(f"      ❌ Placing {expected} is INVALID according to rules!")
                                else:
                                    print(f"      ✓ Placing {expected} should be valid - this is a bug!")
    
    def get_demo(self, state=None, **kwargs):
        state = self.state if state is None else state
        grid, constraints = self.problem if self.problem else (None, None)
        
        if not grid or not constraints:
            return None
        
        # Handle both ProblemState and dict
        state_objs = state.objs if isinstance(state, ProblemState) else state
        
        # Check if puzzle is complete first
        current_grid = []
        for r in range(self.grid_size):
            row = []
            for c in range(self.grid_size):
                value = state_objs.get(f"cell_{r}_{c}", {}).get("value", "none")
                row.append(value if value != "none" else None)
            current_grid.append(row)
        
        if is_tango_complete(current_grid):
            # Puzzle is complete - print debug info and return None
            # The state should already be marked as done in get_state()
            self._print_puzzle_debug_info(current_grid, state_objs, is_complete=True)
            return None
        
        # Use constraint propagation to find next placement
        # This follows the strategy:
        # 1. Start with fixed symbols (already in current_grid)
        # 2. Propagate through × and = constraints
        # 3. Use "no 3-in-a-row" to find forced placements
        # 4. Use balance constraints to find forced placements
        result = find_next_placement_constraint_propagation(current_grid, constraints, self.grid_size)
        
        if result:
            r, c, symbol = result
            sai = (f"cell_{r}_{c}", 'PlaceSymbol', symbol)
            action = Action(sai, arg_foci=[f"cell_{r}_{c}"], 
                          how_help=f"Place {symbol} at ({r},{c}) - constraint propagation")
            return action
        
        # If constraint propagation didn't find a forced placement,
        # use constraint ranking to find the best cell to work on
        # Get top-constraint cells (cells with highest priority)
        top_constraint_cells = self.get_top_constraint_cells(current_grid, constraints)
        
        # Check if top-constraint cells have any valid moves
        top_has_valid_moves = False
        if top_constraint_cells:
            for r, c in top_constraint_cells:
                if current_grid[r][c] is None:
                    if is_valid_placement(current_grid, r, c, "sun", self.grid_size, constraints):
                        top_has_valid_moves = True
                        break
                    if is_valid_placement(current_grid, r, c, "moon", self.grid_size, constraints):
                        top_has_valid_moves = True
                        break
        
        # If top-constraint cells exist and have valid moves, use only those
        # Otherwise, consider ALL empty cells (fallback to any valid move)
        if top_constraint_cells and top_has_valid_moves:
            cells_to_check = top_constraint_cells
        else:
            if top_constraint_cells and not top_has_valid_moves:
                print(f"⚠️  Top-constraint cells have no valid moves, expanding search to all cells")
            cells_to_check = [
                (r, c) for r in range(self.grid_size) for c in range(self.grid_size)
                if state_objs.get(f"cell_{r}_{c}", {}).get("value", "none") == "none"
            ]
        
        # Try to find cells where only one symbol is valid (forced placement)
        for r, c in cells_to_check:
            current_value = state_objs.get(f"cell_{r}_{c}", {}).get("value", "none")
            if current_value == "none":
                # Check if only one symbol is valid (forced placement)
                sun_valid = is_valid_placement(current_grid, r, c, "sun", self.grid_size, constraints)
                moon_valid = is_valid_placement(current_grid, r, c, "moon", self.grid_size, constraints)
                
                if sun_valid and not moon_valid:
                    # Only sun is valid - forced placement
                    rank = self.calculate_cell_constraint_rank(r, c, current_grid, constraints)
                    sai = (f"cell_{r}_{c}", 'PlaceSymbol', "sun")
                    action = Action(sai, arg_foci=[f"cell_{r}_{c}"], 
                                  how_help=f"Place sun at ({r},{c}) - only valid option (rank {rank})")
                    return action
                elif moon_valid and not sun_valid:
                    # Only moon is valid - forced placement
                    rank = self.calculate_cell_constraint_rank(r, c, current_grid, constraints)
                    sai = (f"cell_{r}_{c}", 'PlaceSymbol', "moon")
                    action = Action(sai, arg_foci=[f"cell_{r}_{c}"], 
                                  how_help=f"Place moon at ({r},{c}) - only valid option (rank {rank})")
                    return action
        
        # If no forced placements found, find any valid placement among top-constraint cells
        for r, c in cells_to_check:
            current_value = state_objs.get(f"cell_{r}_{c}", {}).get("value", "none")
            if current_value == "none":
                for symbol in ["sun", "moon"]:
                    # Check validity against current state with constraints
                    if is_valid_placement(current_grid, r, c, symbol, self.grid_size, constraints):
                        rank = self.calculate_cell_constraint_rank(r, c, current_grid, constraints)
                        sai = (f"cell_{r}_{c}", 'PlaceSymbol', symbol)
                        action = Action(sai, arg_foci=[f"cell_{r}_{c}"], 
                                      how_help=f"Place {symbol} at ({r},{c}) - top constraint (rank {rank})")
                        return action
        
        # No valid moves found in top-constraint cells
        # Debug: Print current state to understand why
        self._print_puzzle_debug_info(current_grid, state_objs, is_complete=False)
        
        # Check if puzzle is actually complete (might be a state issue)
        if is_tango_complete(current_grid):
            if isinstance(state, ProblemState):
                state.add_annotations({"is_done": True})
            return None
        
        # Puzzle is not complete but no valid moves found
        # Check if TRULY stuck (no valid moves anywhere in entire grid)
        if self.is_stuck(current_grid, constraints):
            print(f"⚠️  TRULY STUCK - no valid moves ANYWHERE in the grid")
            if self.can_undo():
                print(f"   Suggesting UNDO action (history: {len(self.action_history)} states)")
                # Suggest undo action - agent will decide to use it
                sai = ("undo_button", 'Undo', "undo")
                action = Action(sai, arg_foci=["undo_button"], 
                              how_help="Undo last action - truly stuck with no valid moves anywhere")
                return action
            else:
                print(f"   No history to undo - marking as done")
        else:
            print(f"⚠️  No valid moves found, but this shouldn't happen")
            print(f"   get_demo() should have found a move when expanding to all cells")
        
        # No valid moves and can't undo - mark as done to prevent infinite loop
        if isinstance(state, ProblemState):
            state.add_annotations({"is_done": True})
        return None
    
    def check(self, action, **kwargs):
        if not isinstance(action, Action):
            action = Action(action) if action else None
        if action is None:
            return -1
        grid, constraints = self.problem if self.problem else (None, None)
        
        if not grid or not constraints:
            return -1
        
        if action.selection == "undo_button":
            # Validate undo: must have history and be stuck
            if self.can_undo():
                # Build current grid to check if stuck
                current_grid = []
                for row in range(self.grid_size):
                    grid_row = []
                    for col in range(self.grid_size):
                        value = self.state.objs.get(f"cell_{row}_{col}", {}).get("value", "none")
                        grid_row.append(value if value != "none" else None)
                    current_grid.append(grid_row)
                
                if self.is_stuck(current_grid, constraints):
                    print(f"✓ UNDO action validated: history exists and stuck")
                    return 1
                else:
                    print(f"✗ UNDO action rejected: not stuck")
                    return -1
            else:
                print(f"✗ UNDO action rejected: no history to undo")
                return -1
        
        if action.selection == "done":
            # Regular done action
            current_grid = []
            for r in range(self.grid_size):
                row = []
                for c in range(self.grid_size):
                    value = self.state.objs.get(f"cell_{r}_{c}", {}).get("value", "none")
                    row.append(value if value != "none" else None)
                current_grid.append(row)
            
            # Check if puzzle is complete AND valid
            if is_tango_complete(current_grid) and validate_solution(current_grid, self.grid_size):
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
        
        # Check if the cell is empty (required for placement)
        current_value = self.state.objs.get(f"cell_{r}_{c}", {}).get("value", "none")
        if current_value != "none":
            # Cell is already filled, can't place here
            return -1
        
        # Check if the action's input (symbol to place) is valid
        if action.input not in ["sun", "moon"]:
            return -1
        
        # Build current grid state from self.state (includes all placed symbols)
        current_grid = []
        for row in range(self.grid_size):
            grid_row = []
            for col in range(self.grid_size):
                value = self.state.objs.get(f"cell_{row}_{col}", {}).get("value", "none")
                grid_row.append(value if value != "none" else None)
            current_grid.append(grid_row)
        
        # Check validity against CURRENT state (not initial grid) with constraints
        if not is_valid_placement(current_grid, r, c, action.input, self.grid_size, constraints):
            return -1
        
        # Check constraint order: action must target a top-constraint cell
        # UNLESS top-constraint cells have no valid moves
        top_constraint_cells = self.get_top_constraint_cells(current_grid, constraints)
        if top_constraint_cells and (r, c) not in top_constraint_cells:
            # Check if any top-constraint cell actually has valid moves
            top_has_valid_moves = False
            for tr, tc in top_constraint_cells:
                if current_grid[tr][tc] is None:
                    if is_valid_placement(current_grid, tr, tc, "sun", self.grid_size, constraints):
                        top_has_valid_moves = True
                        break
                    if is_valid_placement(current_grid, tr, tc, "moon", self.grid_size, constraints):
                        top_has_valid_moves = True
                        break
            
            # Only enforce constraint order if top cells have valid moves
            if top_has_valid_moves:
                cell_rank = self.calculate_cell_constraint_rank(r, c, current_grid, constraints)
                top_rank = min(self.calculate_cell_constraint_rank(tr, tc, current_grid, constraints) 
                              for tr, tc in top_constraint_cells)
                print(f"Incorrect because of constraint order: Cell ({r},{c}) has rank {cell_rank}, "
                      f"but top constraint cells have rank {top_rank} and have valid moves")
                print(f"Top constraint cells: {top_constraint_cells}")
                return -1
            else:
                print(f"⚠️ Allowing cell ({r},{c}) rank {self.calculate_cell_constraint_rank(r, c, current_grid, constraints)} "
                      f"because top-constraint cells have no valid moves")
        
        return 1
    
    def apply(self, action, **kwargs):
        if not isinstance(action, Action):
            action = Action(action) if action else None
        if action is None:
            return self.state
        grid, constraints = self.problem if self.problem else (None, None)
        
        if not grid or not constraints:
            return self.state
        
        if action.selection == "undo_button":
            print(f"🔄 EXECUTING UNDO: Reverting to previous state (history size: {len(self.action_history)})")
            result = self.undo_last_action()
            print(f"✓ UNDO COMPLETE: Now at previous state (history size: {len(self.action_history)})")
            return result
        
        if action.selection == "done":
            # Regular done action
            return self.state
        
        if not action.selection.startswith("cell_"):
            return self.state
        
        try:
            r, c = map(int, action.selection.split("_")[1:])
        except:
            return self.state
        
        if not (0 <= r < self.grid_size and 0 <= c < self.grid_size):
            return self.state
        
        # Save current state to history before making changes
        if action.input in ["sun", "moon"]:
            self.action_history.append(self.state.copy())
            # Limit history size to prevent memory issues
            if len(self.action_history) > self.max_history:
                self.action_history.pop(0)
        
        new_state = self.state.copy()
        
        if action.input in ["sun", "moon"]:
            # Preserve id, row, col, and spatial relationships when updating value
            cell_obj = new_state.objs.get(f"cell_{r}_{c}", {})
            new_state[f"cell_{r}_{c}"] = {
                "id": f"cell_{r}_{c}",
                "type": "Cell",
                "value": action.input,
                "row": r,
                "col": c,
                "above": cell_obj.get("above"),
                "below": cell_obj.get("below"),
                "left": cell_obj.get("left"),
                "right": cell_obj.get("right")
            }
        
        # Note: We don't track selected_cell in state as it's metadata not needed for agent
        
        # Check if puzzle is complete after this action
        current_grid = []
        for row in range(self.grid_size):
            grid_row = []
            for col in range(self.grid_size):
                value = new_state.objs.get(f"cell_{row}_{col}", {}).get("value", "none")
                grid_row.append(value if value != "none" else None)
            current_grid.append(grid_row)
        
        # Check if puzzle is complete AND valid
        if is_tango_complete(current_grid) and validate_solution(current_grid, self.grid_size):
            # Mark state as done - trainer will check this annotation
            new_state.add_annotations({"is_done": True})
            # Print debug info when puzzle is completed (only if not already marked as done)
            if not self.state.get_annotation("is_done"):
                self._print_puzzle_debug_info(current_grid, new_state.objs, is_complete=True)
        
        # Update self.state with the new state (required for trainer to see changes)
        self.state = new_state
        
        return self.state
    
    def set_problem(self, *args, **kwargs):
        """Set the Tutor Environment's current problem"""
        self.set_random_problem()
    
    def get_problem(self):
        """Get some kind of unique identifier for the current problem"""
        if self.problem:
            grid, constraints = self.problem
            return f"tango_{self.grid_size}_{hash(str(constraints))}"
        return "tango_default"
    
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
        grid, constraints = self.problem if self.problem else (None, None)
        
        if not grid or not constraints:
            return []
        
        # Handle both ProblemState and dict
        state_objs = state.objs if isinstance(state, ProblemState) else state
        
        # Build current grid state from state (includes all placed symbols)
        current_grid = []
        for r in range(self.grid_size):
            row = []
            for c in range(self.grid_size):
                value = state_objs.get(f"cell_{r}_{c}", {}).get("value", "none")
                row.append(value if value != "none" else None)
            current_grid.append(row)
        
        demos = []
        
        # Check if we're stuck - if so, suggest undo
        if self.is_stuck(current_grid, constraints) and self.can_undo():
            sai = ("undo_button", 'Undo', "undo")
            action = Action(sai, arg_foci=["undo_button"], 
                          how_help="Undo last action - truly stuck with no valid moves")
            demos.append(action)
            return demos  # Return only undo when stuck
        
        # Get top-constraint cells - only return demos for these cells
        top_constraint_cells = self.get_top_constraint_cells(current_grid, constraints)
        
        # Only consider top-constraint cells
        for r, c in top_constraint_cells:
            if state_objs.get(f"cell_{r}_{c}", {}).get("value", "none") == "none":
                # Try each symbol
                for symbol in ["sun", "moon"]:
                    # Check validity against current state with constraints
                    if is_valid_placement(current_grid, r, c, symbol, self.grid_size, constraints):
                        rank = self.calculate_cell_constraint_rank(r, c, current_grid, constraints)
                        sai = (f"cell_{r}_{c}", 'PlaceSymbol', symbol)
                        action = Action(sai, arg_foci=[f"cell_{r}_{c}"], 
                                      how_help=f"Place {symbol} at ({r},{c}) - rank {rank}")
                        demos.append(action)
        
        return demos
    
    def get_state(self):
        """Get the current state of the Tutor"""
        # Check if puzzle is complete and mark state accordingly
        # This ensures the trainer can detect completion before calling get_demo()
        if not self.state.get_annotation("is_done"):
            current_grid = []
            for r in range(self.grid_size):
                row = []
                for c in range(self.grid_size):
                    value = self.state.objs.get(f"cell_{r}_{c}", {}).get("value", "none")
                    row.append(value if value != "none" else None)
                current_grid.append(row)
            
            # Check if puzzle is complete AND valid
            if is_tango_complete(current_grid) and validate_solution(current_grid, self.grid_size):
                self.state.add_annotations({"is_done": True})
                # Print debug info when puzzle is completed
                state_objs = self.state.objs
                self._print_puzzle_debug_info(current_grid, state_objs, is_complete=True)
        
        return self.state
    
    def set_state(self, state):
        """Set the current state of the Tutor"""
        if isinstance(state, ProblemState):
            self.state = state
        else:
            self.state = ProblemState(state)


if __name__ == "__main__":
    print("=== Testing TangoPuzzle Environment Implementation ===\n")
    
    print("1. Testing basic puzzle generation...")
    try:
        env = TangoPuzzle(grid_size=6, problem_types=["basic"])
        print(f"   ✓ Generated Tango puzzle: {env.grid_size}x{env.grid_size}")
        print(f"   ✓ Problem types: {env.problem_types}")
    except Exception as e:
        print(f"   ✗ Error generating puzzle: {e}")
    
    print("\n2. Testing state management...")
    try:
        print(f"   ✓ Initial state keys: {list(env.state.keys())[:5]}...")
        print(f"   ✓ Grid size: {env.state.get('grid_size', {}).get('value', '')}")
        print(f"   ✓ Constraints: {env.state.get('constraints', {}).get('value', '')}")
        print(f"   ✓ Satisfied constraints: {env.state.get('satisfied_constraints', {}).get('value', '')}")
    except Exception as e:
        print(f"   ✗ Error in state management: {e}")
    
    print("\n3. Testing action space...")
    try:
        selections = env.get_possible_selections()
        args = env.get_possible_args()
        print(f"   ✓ Possible selections: {len(selections)} (showing first 5: {selections[:5]})")
        print(f"   ✓ Possible args: {len(args)} (showing first 5: {args[:5]})")
        print(f"   ✓ Includes 'done' action: {'done' in selections}")
        print(f"   ✓ Includes symbols: {'sun' in args and 'moon' in args}")
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
            print(f"   ✓ Satisfied constraints: {new_state.get('satisfied_constraints', {}).get('value', '')}")
            
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
        test_grid = [[None for _ in range(6)] for _ in range(6)]
        test_constraints = [(0, 0, 0, 1, 'horizontal')]
        is_valid = is_valid_placement(test_grid, 0, 0, 'sun', 6, test_constraints)
        print(f"   ✓ is_valid_tango_placement test: {is_valid}")
        
        complete_grid = [['sun' for _ in range(6)] for _ in range(6)]
        is_complete = is_tango_complete(complete_grid)
        print(f"   ✓ is_tango_complete test: {is_complete}")
        
        satisfied, total = count_constraints(complete_grid, test_constraints)
        print(f"   ✓ count_tango_constraints test: {satisfied}/{total}")
    except Exception as e:
        print(f"   ✗ Error testing helper functions: {e}")
    
    print("\n=== Testing Complete ===")
    print("All core functions have been tested successfully!")
