from anthropic import Anthropic
from tutorgym.eval.llm_evaluator_base import LLMEvaluator

class AnthropicEvaluator(LLMEvaluator):
    def __init__(self, tutor_kind):
        super().__init__("anthropic", tutor_kind)
        self.client = Anthropic()
        
    def get_completion(self, prompt, max_tokens=100):
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

if __name__ == "__main__":
    evaluator = AnthropicEvaluator("apprentice")
    evaluator.evaluate()
