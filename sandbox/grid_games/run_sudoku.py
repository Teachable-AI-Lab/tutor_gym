import argparse
from tutorgym.trainer import AuthorTrainer
from tutorgym.utils import DataShopLogger
from tutorgym.agents.oracle_agent import OracleAgent
from sudoku_env import SudokuPuzzle


def run_environment(grid_size=9, problem_types=["easy", "medium", "hard"], n_problems=20, problem_set=[]):
    """
    Run the Sudoku puzzle environment
    
    Args:
        grid_size: Size of the grid (must be 9, default: 9)
        problem_types: List of problem types (default: ["easy", "medium", "hard"])
        n_problems: Number of problems to run
        problem_set: Optional list of specific problems
    """
    domain_name = f"sudoku_{grid_size}x{grid_size}"
    
    logger = DataShopLogger(domain_name, extra_kcs=['field'], output_dir=f'log_{domain_name}_author')
    env = SudokuPuzzle(grid_size=grid_size, problem_types=problem_types)

    agent = OracleAgent(env)
    trainer = AuthorTrainer(agent, env, logger=logger,
                problem_set=problem_set, n_problems=n_problems)
    trainer.start()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run Sudoku puzzle environment')
    parser.add_argument('--grid-size', type=int, default=9,
                      help='Size of the grid (must be 9, default: 9)')
    parser.add_argument('--problems', type=int, default=20,
                      help='Number of problems to run (default: 20)')
    parser.add_argument('--problem-types', type=str, nargs='+', default=["easy", "medium", "hard"],
                      help='Problem types to use (default: ["easy", "medium", "hard"])')
    
    args = parser.parse_args()
    run_environment(grid_size=args.grid_size, problem_types=args.problem_types, n_problems=args.problems)
    
    # Uncomment to test with different configurations:
    # run_environment(grid_size=9, problem_types=["easy"], n_problems=1)
    # run_environment(grid_size=9, problem_types=["medium"], n_problems=1)

