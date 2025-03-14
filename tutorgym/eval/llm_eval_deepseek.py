import requests
from tutorgym.eval.llm_eval import LLMEvaluator

class DeepseekEvaluator(LLMEvaluator):
    def __init__(self, tutor_kind):
        super().__init__("deepseek", tutor_kind)
        
    def run_prompt(self, prompt, max_tokens=100):
        response = requests.post('http://localhost:11434/api/generate', json={
            'model': 'deepseek-v2.5',
            'prompt': prompt,
            'stream': False,
            'options': {
                'num_ctx': 4096
            }
        })

        if(response.status_code >= 300):
            error = response.json()['error']
            raise ConnectionError(f"Status Code:{response.status_code}, Error: {error}")
        else:
            response = response.json()['response']
        return response

if __name__ == "__main__":
    evaluator = DeepseekEvaluator()
    evaluator.evaluate()
