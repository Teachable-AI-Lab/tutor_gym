from tutorgym.utils import unique_hash
from tutorgym.shared import Action
import json

print()
n_lines = 0
with open("apprentince_compl.prof", 'r') as profile:
    while line := profile.readline():
        obj = json.loads(line)
        print("---", obj["domain"], obj["problem"], obj['scaffold'], "---")
        
        # A unique hash of the completeness profile line
        print("UNIQUE HASH", unique_hash(line))

        # Just printing stuff you'll need, format however you want
        print("STATE:")
        for key, elem in obj["state"].items():
            print(f"{'[L] ' if elem.get('locked',False) else '    '}{elem['id']}: {elem.get('value',None)}")
            
        print(len(obj['correct_actions']), "CORRECT")
        for c_action in obj['correct_actions']:
            #print(f"    {c_action['selection']}->{c_action['inputs']['value']}")
            print(f"    {Action(c_action)}")
            
        print(len(obj['incorrect_actions']), "INCORRECT")
        for i_action in obj['incorrect_actions']:
            print(f"    {Action(i_action)}")
            #print(f"    {i_action['selection']}->{i_action['inputs']['value']}")

        #####  TODO   ###### 
        # For each profile line ask the LLM 
        # 1. What is the next correct action? 
        # 2. For each correct action is the action correct?
        # 3. For each incorrect action is the action correct?
        ####################
        
        n_lines += 1
