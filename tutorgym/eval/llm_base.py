from pathlib import Path
import requests
import yaml
import time
import traceback
import sys
from colorama import Back, Fore, Style

action_types_by_tutor_kind = {
    "apprentice" : ["input change", "PressButton"],
    "oatutor" : ["UpdateTextField", "UpdateRadioButton"] ,
    "ctat" : ["UpdateTextField", "PressButton"] ,
}

def print_green(x):
    print(Back.GREEN + Fore.BLACK + str(x) + Style.RESET_ALL)

def print_red(x):
    print(Back.RED + Fore.BLACK + str(x) + Style.RESET_ALL)

def print_white(x):
    print(Back.WHITE + Fore.BLACK + str(x) + Style.RESET_ALL)

def print_response(reasoning, last_line, duration):
    print("RESPONSE:")
    print(reasoning.encode(sys.stdout.encoding, 'replace'))
    print_white(last_line.encode(sys.stdout.encoding, 'replace').decode("utf-8"))
    print(f"Duration: {duration / 1e9:.4f} seconds")

class LLMPromptable():
    def __init__(self, 
                 tutor_kind, 
                 client,
                 model,
                 client_url=None,
                 context_length=4096,
                 prompt_retries=10,
                 prompt_retry_delay=5,
                 resp_last_line_only=True, 
                 **kwargs):
        
        self.tutor_kind = tutor_kind
        self.client_name = client.lower()

        assert self.client_name in ("anthropic", "ollama", "openai")
        if(self.client_name == "anthropic"):
            from anthropic import Anthropic
            self.client_inst = Anthropic()
        elif(self.client_name == "openai"):
            from openai import OpenAI
            if client_url:
                self.client_inst = OpenAI(base_url=client_url, api_key="EMPTY")
            else:
                self.client_inst = OpenAI()

        self.model = model
        self.client_url = client_url
        self.context_length = context_length
        self.prompt_retries = prompt_retries
        self.prompt_retry_delay = prompt_retry_delay
        self.resp_last_line_only = resp_last_line_only

        prompts_path = Path(__file__).parent / "prompts.yaml"
        with open(prompts_path, 'r') as f:
            self.prompts = yaml.safe_load(f)

        examples_path = Path(__file__).parent / "action_type_examples.yaml"
        with open(examples_path, 'r') as f:
            self.action_type_examples = yaml.safe_load(f)

        self.action_types = action_types_by_tutor_kind[self.tutor_kind]
        example_prompts = [self.action_type_examples[a_t] for a_t in self.action_types]
        self.action_type_examples_prompt = self.prompts['action_examples'].format(
            action_types=self.action_types,
            examples="\n".join(example_prompts)
        )

    def send_prompt_ollama(self, prompt):
        print("Prompt length:", len(prompt))
        request_resp = requests.post(self.client_url, json={
            'model': self.model,
            'prompt': prompt,
            'stream': False,
            'options': {
                'num_ctx': self.context_length
            }
        })

        if(request_resp.status_code >= 300):
            error = request_resp.json()['error']
            raise ConnectionError(f"Status Code:{request_resp.status_code}, Error: {error}")
        else:
            resp_json = request_resp.json()
            response = resp_json['response']
            duration = resp_json['total_duration']
            print("CONTEXT LENGTH:", len(resp_json['context']))

        return response, duration
        
    def send_prompt_anthropic(self, prompt):
        t0 = time.time_ns()/float(1e9)
        response = self.client_inst.messages.create(
            model=self.model,#"claude-3-5-sonnet-20241022",
            max_tokens=self.context_length,
            messages=[{"role": "user", "content": prompt}]
        )
        t1 = time.time_ns()/float(1e9)
        return response.content[0].text, t1-t0

    def send_prompt_openai(self, prompt):
        t0 = time.time_ns()/float(1e9)
        response = self.client_inst.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=self.context_length,
            temperature=0
        )
        t1 = time.time_ns()/float(1e9)
        return response.choices[0].message.content, t1-t0

    def run_prompt(self, prompt):
        """Get response from the LLM"""        
        send_prompt = getattr(self, f"send_prompt_{self.client_name}")
        response, duration = send_prompt(prompt)

        if(self.resp_last_line_only):
            reasoning = "\n".join(response.split("\n")[:-1])
            response = response.split("\n")[-1]
        else:
            reasoning = ""

        print_response(reasoning, response, duration)
        
        return response

    def run_prompt_retry(self, prompt):
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

