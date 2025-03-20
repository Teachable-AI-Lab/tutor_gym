from pathlib import Path
from tutorgym.env_classes.oatutor.oa_tutors import OATutor
from tutorgym.trainer import AuthorTrainer
from tutorgym.agents.oracle_agent import OracleAgent
from tutorgym.helpers.collect_problems import collect_oatutor_problems

def main():
    # Read problem names from file
    # current_dir = Path(__file__).parent
    # problem_names_file = current_dir / '../../tutorgym/envs/oatutor/ProblemNames.txt'
    # with open(problem_names_file, 'r') as file:
    #     problem_names = [line.strip() for line in file if line.strip()]
    

    # problems = [{"problem_name" : p} for p in problem_names]
    problems = collect_oatutor_problems()
    env = OATutor()
    agent = OracleAgent(env)
    trainer = AuthorTrainer(agent, env, problem_set=problems)
    trainer.start()

    # Loop through each problem
    # for problem_name in problem_names:
    #     print(f"\nRunning tutor for problem: {problem_name}")
        # OATutor.set_problem(problem_name)
        

if __name__ == "__main__":
    main()
