from pathlib import Path
from tutorgym.env_classes.oa_tutors import OATutor
from tutorgym.trainer import AuthorTrainer
from tutorgym.oracle_agent import OracleAgent

def main():
    # Read problem names from file
    current_dir = Path(__file__).parent
    problem_names_file = current_dir / '../../tutorgym/envs/oa_tutors/ProblemNames.txt'
    with open(problem_names_file, 'r') as file:
        problem_names = [line.strip() for line in file if line.strip()]
    
    # Loop through each problem
    for problem_name in problem_names[:2]:
        print(f"\nRunning tutor for problem: {problem_name}")
        env = OATutor(problem_name=problem_name)
        agent = OracleAgent(env)
        trainer = AuthorTrainer(agent, env, n_problems=20)
        trainer.start()

if __name__ == "__main__":
    main()
