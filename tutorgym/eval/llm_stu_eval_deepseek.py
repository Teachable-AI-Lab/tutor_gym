from tutorgym.trainer import AuthorTrainer, Trainer
from tutorgym.utils import DataShopLogger
from tutorgym.agents.oracle_agent import RandomOracleAgent, OracleAgent
from tutorgym.agents.agent_api import AbstactAgent
# from tutorgym.envs.apprentice_tutors.tutor import AllTutorContainer
from tutorgym.env_classes.CTAT.CTAT_tutor import CTAT_Tutor
from tutorgym.env_classes.apprentice_tutor import ApprenticeTutor
from tutorgym.envs.apprentice_tutors.env_registry import ENVIRONMENTS 
from tutorgym.shared import Action
import requests

class LLMStudentAgent():
    def __init__(self, **kwargs):
        # Remove Anthropic client, just keep conversation log
        self.conversation_log = []
        self.max_chars = 100000
        
    def _manage_conversation_log(self):
        total_chars = sum(len(msg["content"]) for msg in self.conversation_log)
        if total_chars > self.max_chars:
            print(total_chars)
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
        prompt = f"""
{state.objs}
What should be the next action in this state for? You are only only allowed to changed a field with 'locked' as False \
I need your response in this format: field;action_type;value, where:
1. field is name of the field. 
2. action_type can either be either "input change" or "PressButton"
3. value is the value to enter that field. 
At tops, give a single expression for value or a single word. Avoid additional text.
        """
        
        self.conversation_log.append({"role": "user", "content": prompt})
        self._manage_conversation_log()
        
        try:
            messages = "\n\n".join([msg["content"] for msg in self.conversation_log])
            response = requests.post('http://localhost:11434/api/generate', json={
                'model': 'deepseek-v2.5',
                'prompt': messages,
                'stream': False,
                'options': {
                    'num_ctx': 4096
                }
            })
            
            # Parse response into an Action
            action_text = response.json()['response']
            parts = action_text.split(';')
            if len(parts) == 3:                
                selection, action_type, input = parts
                if action_type == "PressButton":
                    input = -1
            else:
                raise ValueError("Incorrect format in response")
        except Exception as e:
            print(f"LLM failed with error: {str(e)}")
            import time
            time.sleep(1)  # Sleep for 1 second on failure
            selection, action_type, input = 'incorrect_format', 'incorrect_format', 'incorrect_format'
        
        action = Action((selection, action_type, {'value': input.replace('\\\\', '\\') if type(input) == str else input}))        
        return action

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
                extra_kcs=['field'], output_dir=f'log_LLM_stu_agents_deepseek')  # Changed log directory name
    env = ApprenticeTutor(scaffold=scaffold)

    #### Replace This w/ your LLM Agent ####
    agent = LLMStudentAgent()
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
        tutor_set = generate_apprentice_problem_set(
            [tutor],
            10,
        )      
        problem_set += tutor_set
    run_training(problem_set) 

