from openai import OpenAI
from tutorgym.eval.llm_evaluator_base import LLMEvaluator

class OpenAIEvaluator(LLMEvaluator):
    def __init__(self):
        super().__init__("openai")
        self.client = OpenAI()
        
    def get_completion(self, prompt, max_tokens=100):
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0
        )
        return response.choices[0].message.content

if __name__ == "__main__":
    evaluator = OpenAIEvaluator()
    evaluator.evaluate("apprentice_compl.prof")