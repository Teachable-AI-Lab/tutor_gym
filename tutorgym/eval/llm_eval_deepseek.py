import requests
from tutorgym.eval.llm_evaluator_base import LLMEvaluator

class DeepseekEvaluator(LLMEvaluator):
    def __init__(self, tutor_kind):
        super().__init__("deepseek", tutor_kind)
        
    def get_completion(self, prompt, max_tokens=100):
        response = requests.post('http://honor.cc.gatech.edu:11434/api/generate', json={
            'model': 'deepseek-v2.5',
            'prompt': prompt,
            'stream': False,
            'options': {
                'num_ctx': 4096
            }
        })
        return response.json()['response']

if __name__ == "__main__":
    evaluator = DeepseekEvaluator()
    evaluator.evaluate()
