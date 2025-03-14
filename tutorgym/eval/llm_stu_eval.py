from abc import ABC, abstractmethod
from tutorgym.trainer import AuthorTrainer, Trainer
from tutorgym.utils import DataShopLogger
from tutorgym.agents.oracle_agent import RandomOracleAgent, OracleAgent
from tutorgym.agents.agent_api import AbstactAgent
# from tutorgym.envs.apprentice_tutors.tutor import AllTutorContainer
from tutorgym.env_classes.CTAT.CTAT_tutor import CTAT_Tutor
from tutorgym.env_classes.apprentice_tutor import ApprenticeTutor
from tutorgym.envs.apprentice_tutors.env_registry import ENVIRONMENTS 
from tutorgym.shared import Action
from pathlib import Path
import requests
import yaml
import time
import traceback


class LLMStudentAgent(ABC):
    def __init__(self, prompt_retries=10, prompt_retry_delay=5, **kwargs):
        # Remove Anthropic client, just keep conversation log
        self.conversation_log = []
        self.max_chars = 100000
        self.prompt_retries = prompt_retries
        self.prompt_retry_delay = prompt_retry_delay

        prompts_path = Path(__file__).parent / "prompts.yaml"
        with open(prompts_path, 'r') as f:
            self.prompts = yaml.safe_load(f)

    def run_retry_prompt(self, prompt):
        attempt_n = 0
        while True:
        # for attempt_n in range(self.prompt_retries)
            try:
                response = self.run_prompt(prompt)
                return response
            except Exception as e:
                if(attempt_n < self.prompt_retries):
                    print("LLM API has failed with:", e)
                    print(f"Retrying in {float(self.prompt_retry_delay)} seconds.")
                    time.sleep(self.prompt_retry_delay)
                    attempt_n += 1
                else:
                    traceback.print_exc()
                    input(f"LLM API reattempted {self.prompt_retries} times. "+
                            "The final attempt produced the error above. "+
                            "\n\tPress any key to retry...")
                    attempt_n = 0


    @abstractmethod
    def run_prompt(self, prompt):
        """Get response from the LLM"""
        pass
        
    def _manage_conversation_log(self):
        total_chars = sum(len(msg["content"]) for msg in self.conversation_log)
        if total_chars > self.max_chars:
            print("total_chars:", total_chars)
            self.conversation_log = self.conversation_log[3:]
            
    def train(self, state, action, reward, is_demo=False, is_start=False, **kwargs):
        if is_demo:
            message = f"For this step, the correct action is: {action}"
            self.conversation_log.append({"role": "user", "content": message})
        else:
            self.conversation_log.append({"role": "assistant", "content": f"This is my action: {action}"})
            if reward <= 1:
                message = f"That action was incorrect. The correct action was: {action}"
            else:
                message = "That action was correct!"
            self.conversation_log.append({"role": "user", "content": message})
        self._manage_conversation_log()

    # def train_all(self, training_set, states={}, **kwargs):

    def act(self, state, is_start=False, **kwargs):
        if is_start:
            self.conversation_log.append({"role": "user", "content": "------Now lets solve this problem!------"})
            
        # Construct prompt for next action
        prob_prompt = self.prompts['student_act']['template'].format(state=state.objs)
        
        self.conversation_log.append({"role": "user", "content": prob_prompt})
        self._manage_conversation_log()

        full_prompt = "\n\n".join([msg["content"] for msg in self.conversation_log])

        response = self.run_retry_prompt(full_prompt)

        # Parse response into an Action
        # action_text = response.json()['response']
        parts = response.split(';')
        if len(parts) == 3:                
            selection, action_type, input = parts
            if action_type == "PressButton":
                input = -1
        else:
            selection, action_type, input = 'incorrect_format', 'incorrect_format', 'incorrect_format'
        
        action = Action((selection, action_type, {'value': input.replace('\\\\', '\\') if type(input) == str else input}))        
        return action

    # def act_all(self, state, **kwargs):

class DeepSeekStudentAgent(LLMStudentAgent):
    def run_prompt(self, prompt):
        response = requests.post('http://localhost:11434/api/generate', json={
            'model': 'deepseek-v2.5',
            'prompt': prompt,
            'stream': False,
            'options': {
                'num_ctx': 4096
            }
        })
        response = response.json()['response']
        print(prompt)
        print("RESPOSNE:", response)
        return response


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


def run_training(problem_set, tutor_kind, model, scaffold="first"):    
    logger = DataShopLogger("LLM_Agents",
                extra_kcs=['field'], output_dir=f'stu_eval_logs/{tutor_kind}_{model}')  # Changed log directory name
    env = ApprenticeTutor(scaffold=scaffold)

    #### Replace This w/ your LLM Agent ####
    agent = DeepSeekStudentAgent()
    ####################################### 

    trainer = Trainer(agent, env, logger=logger,
                problem_set=problem_set,
                num_incorrect_force_demo=2)

    # print("START", problem_set)
    trainer.start()
    print("STOP")


if __name__ == "__main__":
    d = {'htn_factor_grouping': 12, 'htn_factor_leading_one': 15, 'htn_factor_slip_slide': 10, 'htn_logarithmic_equations_solve_algebraically_before_after': 4, 'htn_logarithms_quotient': 8, 'htn_quadratic_equations_identify_coeffs': 2, 'htn_radicals_product_rule': 4, 'htn_logarithms_power': 6, 'htn_exponents_product': 8, 'htn_quadratic_equations_solve_using_factors': 2, 'htn_radicals_adding_square_roots': 2, 'htn_radicals_quotient_rule': 5, 'htn_rational_equation_find_domain': 10, 'htn_exponential_equations_different_base': 2, 'htn_exponential_equations_fractional_exponents_common_base': 0, 'htn_logarithmic_equations_solve_algebraically': 4, 'htn_logarithms_product': 10, 'htn_quadratic_equations_factorize': 2, 'htn_exponential_equations_common_base': 2, 'htn_exponential_equations_solve_Aekt': 1, 'htn_logarithmic_equations_solve_using_one_to_one_property': 4, 'htn_quadratic_equations_solve_using_completing_square': 0, 'htn_radicals_subtracting_square_roots': 4, 'htn_quadratic_equations_nature_of_solution': 3, 'htn_exponential_equations_change_to_common_base': 1, 'htn_exponential_equations_solve_quadratic_form': 2, 'htn_quadratic_equations_solve_using_quadratic_formula': 1, 'htn_quadratic_equations_solve_using_square_root_property': 2}

    problem_set = []
    for tutor, n_probs in d.items():
        tutor = tutor.replace("htn_", "")
        tutor_set = generate_apprentice_problem_set(
            [tutor],
            10,
        )      
        problem_set += tutor_set
    run_training(problem_set, 'apprentice', 'deepseek') 

