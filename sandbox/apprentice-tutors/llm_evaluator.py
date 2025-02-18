from tutorgym.envs.apprentice_tutors.tutor import AllTutorContainer
from tutorgym.oracle_agent import OracleAgent
import ast
import openai

from tutorgym.envs.apprentice_tutors.cognitive_models.logarithms import (
    htn_logarithms_product as logarithms_product,
)

openai.api_key = "YOUR_API_KEY"

if __name__ == "__main__":
    env = AllTutorContainer(domain=logarithms_product.Domain, problem_generator=logarithms_product.htn_logarithms_product_rule_problem, problem_types=["power"])
    problem_type = "logarithms_product_rule"
    agent = OracleAgent(env)
    correct, incorrect = 0, 0
    while True:
        string_for_llm = f"""
        I want you to help me solve {problem_type}
You are given state:
{agent.env.state.objs}
equation.value refers to the problem. What do you think should be my next action in the interface?  \
You have two action choices 'PressButton' and 'UpdateTextField'.
I want your answer in this format, \
([string of field value you want to modify], [string of action name], {{value: [value you want to input]}})

Please only give me the answer without any additional text.
        """
        
        response = openai.Completion.create(
            engine="text-davinci-003", 
            prompt=string_for_llm,
            max_tokens=150
        )
        
        llm_response = response.choices[0].text.strip()
        result = ast.literal_eval(llm_response)        
        next_action = agent.env.get_demo()
        if result == next_action:
            correct += 1
        else:
            incorrect += 1
        if agent.env.sai_makes_done(next_action.sai):
            break
        agent.env.apply(next_action)
    total = correct + incorrect
    print(f'PERCENTS(correct:{100*(correct)/total:.2f}%, incorrect:{100*(incorrect)/total:.2f}%)')