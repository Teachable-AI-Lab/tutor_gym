import pandas as pd
import os
import re
import json
filename = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data/data.txt")

# Seems there are a few buggy ones
ignore_problems = {"11=-7-x/3+7"}

elem_map = {
    'JCommTable3_R1' : 'step0',
    'JCommTable_C1R2' : 'lhs1',
    'JCommTable2_C1R2' : 'rhs1',
    'JCommTable3_R2' : 'step1',
    'JCommTable_C1R3' : 'lhs2',
    'JCommTable2_C1R3' : 'rhs2',
    'done' : 'done'
}

split_reg = r'|minus|_equals_|divide|times|\+|\(|\)|[a-zA-Z]|\d+|'


def prob_from_name(name):
    name = name[5:]
    tokens = re.findall(split_reg, name)
    prob = []
    term = ""
    for token in tokens:
        if(token == "minus"):
            term += "-"
        elif(token == "+"):
            term += "+"
        elif(token == "divide"):
            term += "/"
        elif(token == "times"):
            term += "*"
        elif(token == "("):
            term += "("
        elif(token == ")"):
            term += ")"
        elif(token == "_equals_"):
            prob.append(term)
            term = ""
        else:
            term += token
    prob.append(term)
    return prob

act_type_map = {
    "UpdateTable" : "UpdateTextField",
    "ButtonPressed" : "PressButton",
}




df = pd.read_csv(filename, delimiter='\t')
# df = df[['Action', 'Problem Name', 'Step Name', 'Outcome', 'Selection', 'Input']]
# df['Problem Name'] = df['Problem Name'].apply(lambda x: x[2:])
steps_by_problem = {}
for vals, group_df in df.groupby(by=['Problem Name']):
    if vals not in steps_by_problem:
        steps_by_problem[vals] = []
        has_done = False
        for i in range(len(group_df)):
            if group_df.iloc[i]['Outcome'] == 'CORRECT':
                sel = elem_map[group_df.iloc[i]['Selection']]
                act_type = group_df.iloc[i]['Action']
                act_type = act_type_map.get(act_type, act_type)
                inp = group_df.iloc[i]['Input']
                steps_by_problem[vals].append({"name": group_df.iloc[i]['Step Name'], 
                                               "sai" : (sel, act_type, inp),
                                               "KC (Action-typein)" : group_df.iloc[i]['KC (Action-typein)']
                                               })
                if(sel == 'done'):
                    has_done = True
                    break
        if(not has_done or len(steps_by_problem[vals]) < 7):
            del steps_by_problem[vals]


prob_dict = {}
for name, steps in steps_by_problem.items():
    args = lhs, rhs = prob_from_name(name)
    short_name = f"{lhs}={rhs}"
    if(short_name in ignore_problems):
        continue
    prob_dict[short_name] = {"steps":steps}
    print(f"{short_name}:", )
    print([step['sai'][0] for step in steps],
          [step['sai'][2] for step in steps])
    # for step in steps:
    #     print(step)
        # print(f"\t{step[1], step[-1]}")

with open("algebra.json", "w") as outfile:
    json.dump(prob_dict, outfile)
