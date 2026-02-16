"""Agent runner for scaffolding levels.

1. ScaffoldController: Iterates through problems at different scaffolds
   (To be replaced with Jacob's BKT controller)
   
2. run_agent_with_scaffold(): Runs an agent on a problem at a specific scaffold level
   and measures performance
"""

from tutorgym.env_classes.apprentice.apprentice_tutor import ApprenticeTutor
from tutorgym.env_classes.apprentice.test_scaffolding import ScaffoldIterator
import json


class ScaffoldController:
    """
    An iterator that cycles through a list of problems (placeholder for Jacob's future BKT controller)
    """
    
    def __init__(self, problems, scaffold="first", max_cycles=1):
        # Store the list of problems to iterate through
        self.problems = problems
        # Reserve scaffold for future BKT controller (currently unused)
        self.scaffold = scaffold
        # How many complete cycles through the problem list should we do?
        self.max_cycles = max_cycles
        # Track which problem we're on in the current cycle
        self.problem_index = 0
        # Track which cycle we're in
        self.cycle_count = 0
    
    def __iter__(self):
        return self
    
    def __next__(self):
        if self.cycle_count >= self.max_cycles:
            raise StopIteration
        
        problem = self.problems[self.problem_index % len(self.problems)]
        self.problem_index += 1
        
        if self.problem_index >= len(self.problems):
            self.problem_index = 0
            self.cycle_count += 1
        
        return problem


def run_agent_with_scaffold(agent, domain, initial_problem, scaffold="all", max_steps=100, verbose=True):
    """Run an agent on a problem at a specific scaffold level.
    
    This is the main function for running agents and measuring performance.
    When agent=None, this runs the oracle baseline which always knows the correct
    next action and takes it immediately
    
    Args:
        agent: Agent object (currently unused; None runs oracle baseline)
        domain: Domain name (e.g., "exponents_product")
        initial_problem: Problem string (e.g., "5^3 * 5^7")
        scaffold: Scaffold level to test (default "all" for full scaffolding)
        max_steps: Maximum steps to allow before giving up (default 100)
        verbose: Whether to print status updates (default True)
    
    Returns:
        Dict with metrics:
        - domain: Domain name
        - problem: Problem string
        - scaffold: Scaffold level tested
        - steps: Number of steps taken to solve (or attempted)
        - success: True if problem was solved, False otherwise
    """
    env = ApprenticeTutor(
        domain=domain,
        initial_problem=initial_problem,
        # Use "first" as placeholder for "all" since scaffold="all" needs special handling
        scaffold=scaffold if scaffold != "all" else "first"
    )
    
    # If testing "all" (full scaffolding), override after creation
    if scaffold == "all":
        env.scaffold = "all"
    
    if verbose:
        print(f"Running: {domain}/{initial_problem} at {ScaffoldIterator.get_scaffold_name(scaffold)}")
    
    # Initialize metrics tracking dictionary
    metrics = {
        "domain": domain,
        "problem": initial_problem,
        "scaffold": scaffold,
        "steps": 0,
        "success": False,
    }
    
    for step in range(max_steps):
        state = env.get_state()
        
        # Check if problem is solved
        if state.is_done:
            metrics["success"] = True
            metrics["steps"] = step
            if verbose:
                print(f"  ✓ Solved in {step} steps")
            break
        
        # Get all correct next actions from the HTN planner
        actions = env.get_all_demos()
        if not actions:
            break
        
        # Oracle policy: take the first correct action
        # (In a real agent, we'd use agent.select_action(state) instead)
        reward = env.check(actions[0])
        env.apply(actions[0], reward)
        metrics["steps"] = step + 1
    
    # Return performance metrics
    return metrics
