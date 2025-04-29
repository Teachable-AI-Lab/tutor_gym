====================
Configuring LLMS 
====================
In llm_tutor_eval.py and llm_stu_eval.py agent_configs can changed to
add or remove an LLM configuration. For instance:

"deepseek-v2.5" : {
    "client" : "ollama",
    "client_url" : 'http://localhost:11434/api/generate',
    "model" : "deepseek-v2.5",
    "context_length" : 14000,
    "max_prompt_length" : 30000,
}

client : The LLM-Client type llm_base.py supports ollama, openai, and 
         anthropic 
client_url : The url of the client server (if applicable like if using 	
             ollama on your own machine)
model : The model name
context_length : The size of the context window 
max_prompt_length: (stu_eval only) The number of characters of the full 
                    cumulative prompt (with in-context examples) before the 
                    oldest example is removed from the set to fit in the 
                    context window. A 2:5 ratio of context_length to 
                    max_prompt_length usually works without issue. 

====================
Running LLM Tutor Evaluations
====================

To run a tutor evaluation run llm_tutor_eval.py with:
  --tutor-kind: One of (ctat, apprentice, oatutor)
  --profile:    Any <filename>.prof file. Files "-aug" post-fix should
  				be used for final evaluation. 
  --model:      The name of model as specified in agent_configs={} within 
                llm_tutor_eval.py

For example:
python llm_tutor_eval.py --tutor-kind ctat --profile ctat_compl-aug.prof --model deepseek-v2.5
python llm_tutor_eval.py --tutor-kind apprentice --profile apprentice_compl-aug.prof --model deepseek-v2.5
python llm_tutor_eval.py --tutor-kind oatutor --profile oa_compl-aug.prof --model deepseek-v2.5


Logs will be recorded in /tutor_eval_logs. You can view a summary of the 
resutls using: 
python summarize_eval_logs.py --show-all

Where --show-all will show incomplete runs. 


====================
Running LLM Student Evaluations
====================

To run a student evaluation run llm_stu_eval.py with:
  --tutor-kind: One of (ctat, apprentice, oatutor)
  --model:      The name of model as specified in agent_configs={} within 
                llm_stu_eval.py

This mode will run the LLM agent interactively against a tutoring system 
