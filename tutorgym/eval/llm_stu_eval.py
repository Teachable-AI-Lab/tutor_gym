from tutorgym.trainer import AuthorTrainer, Trainer
from tutorgym.utils import DataShopLogger
from tutorgym.agents.oracle_agent import RandomOracleAgent, OracleAgent
from tutorgym.agents.agent_api import AbstactAgent
# from tutorgym.envs.apprentice_tutors.tutor import AllTutorContainer
from tutorgym.env_classes.CTAT.CTAT_tutor import CTAT_Tutor
from tutorgym.env_classes.apprentice_tutor import ApprenticeTutor
from tutorgym.envs.apprentice_tutors.env_registry import ENVIRONMENTS 


class LLMStudentAgent():
    def __init__(self, **kwargs):
        ...


    def train(self, state, action, reward, 
              is_demo=False, is_start=False, **kwargs):
        pass

        if(is_demo):
            # Tell agent something like "this is the correct next action for this step"
            ...
        else:
            # Tell agent something like "yes/no that is correct/incorrect."
            ...

        return # Nothing

    # def train_all(self, training_set, states={}, **kwargs):

    def act(self, state, **kwargs):
    
        if(state.get_annotation("is_start" , False) == True):
            #  At the first step of each problem preceed this question 
            #  with a description of the domain objective and describe its 
            #  role as a student 
            ...

        # Ask agent something like "What should I do at this step?"

        return # An Action()

    # def act_all(self, state, **kwargs):



def generate_apprentice_problem_set(domains, n_problems):
    problem_set = []
    for domain_name in domains:
        if domain_name not in ENVIRONMENTS:
            raise ValueError(f"Environment {domain_name} not found. Available environments: {list(ENVIRONMENTS.keys())}")

        _, problem_generator = ENVIRONMENTS[domain_name]

        for i in range(n_problems):
            problem_set.append({
                "domain": domain_name,
                "initial_problem" : problem_generator(),
                "scaffold" : "first", 
            })

    return problem_set


def run_training(problem_set, scaffold="first"):    
    logger = DataShopLogger("LLM_Agents",
                extra_kcs=['field'], output_dir=f'log_LLM_stu_agents')
    env = ApprenticeTutor(scaffold=scaffold)

    #### Replace This w/ your LLM Agent ####
    agent = RandomOracleAgent(env)
    ####################################### 

    trainer = Trainer(agent, env, logger=logger,
                problem_set=problem_set,
                num_incorrect_force_demo=2)

    print("START", problem_set)
    trainer.start()
    print("STOP")


if __name__ == "__main__":

    problem_set = generate_apprentice_problem_set(
        list(ENVIRONMENTS.keys()),
        10,
    )
    run_training(problem_set)
