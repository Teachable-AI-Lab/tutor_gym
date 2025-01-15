

def _load_profile_line(agent, line):
    import json
    item = json.loads(line)
    profile_sais = [SAI(x) for x in item['sais']]
    state = item['state']
    is_start = len(item['hist'])==0

    if(hasattr(agent, "standardize_state")):
        state = self.standardize_state(state)
        
    return state, item, profile_sais

class ProfileIterator:
    def __init__(self, profile):
        self.profile = profile

        if(isinstance(profile, str)):
            self.profile_list = []
            with open(profile, 'r') as profile_f:
                for line_ind, line in enumerate(profile_f):
                    state, item, profile_sais = _load_profile_line(agent, line)
                self.profile_list.append((state, item, profile_sais))
        elif(isinstance(profile, list)):
            self.profile_list = profile 

    def __iter__(self):
        return self.profile_list

def eval_completeness(agent, profile, verbosity=1, partial_credit=False,
                        print_diff=True, print_correct=False, return_diffs=False,
                        **kwargs):
    ''' Evaluates an agent's correctness and completeness against a completeness profile.'''
    import json, os
    if(verbosity > 0):
        print("--START EVAL COMPLETENESS--")

    profile_iter = profile
    if(not isinstance(profile, ProfileIterator)):
        profile_iter = ProfileIterator(profile)
        
    n_correct, total = 0, 0
    n_first_correct, total_states = 0, 0
    diffs = []
    for state, item, profile_sais in profile_iter:            
        is_start = len(item['hist'])==0

        agent_sais = agent.act_all(state, return_kind='sai',
         is_start=is_start, eval_mode=True)

        # Find the difference of the sets 
        set_agent_sais = set(agent_sais)
        set_profile_sais = set(profile_sais)
        missing = set_profile_sais - set_agent_sais
        extra = set_agent_sais - set_profile_sais
        correct = set_agent_sais.intersection(set_profile_sais)
        n_diff = len(missing) + len(extra)

        diffs.append({"problem": item['problem'], 'hist' : item['hist'], "-": list(missing),"+": list(extra), "=" : list(correct)})

        if(partial_credit):
            total += len(set_profile_sais)
            n_correct += max(0, len(set_profile_sais)-n_diff)
        else:
            total += 1
            n_correct += n_diff == 0

        total_states += 1
        if(len(agent_sais) > 0 and agent_sais[0] in set_profile_sais):
            n_first_correct += 1

    if(print_diff):
        for diff in diffs:
            n_diffs = len(diff['-']) + len(diff['+'])
            
            if(n_diffs != 0):
                print(f"--DIFF: {diff['problem']} {diff['hist']} --")
                for m in diff['-']:
                    print("  -", m['selection'], m['inputs']['value'])
                for m in diff['+']:
                    print("  +", m['selection'], m['inputs']['value'])
            if(print_correct == True or 
               print_correct=="when_diff" and n_diffs > 0):
                for m in diff['=']:
                    print("  =", m['selection'], m['inputs']['value'])    

    completeness = n_correct / total
    correctness = n_first_correct / total_states

    if(verbosity > 0):
        print(f"Correctness : {correctness*100:.2f}%",print_diff)
        print(f"Completeness : {completeness*100:.2f}%")
    out = {"completeness" : completeness, "correctness" : correctness}

    if(return_diffs):
        out['diffs'] = diffs
    return out


class CompletenessEvaluator:
    def __init__(self, log_frequency="after_rollout",
            holdout_profile="",
            print_skills=False, print_htn=False):
        self.log_frequency
        self.holdout_profile = holdout_profile
        self.print_skills = print_skills
        self.print_htn = print_htn

    def set_agent(self, agent):
        self.agent = agent

    def log_completeness(self, holdout_profile='ground_truth.txt', log=[]):
        log.append(eval_completeness(self.agent, self.holdout_profile, 
            print_diff=True, print_correct="when_diff"
        ))

        if(self.print_skills or print_htn):
            print("---------------")
            if(self.print_htn):
                print(self.agent.process_lrn_mech.grammar)
                
            if(self.print_skills):
                for skill in agent.skills.values():
                    print()
                    print(skill)
                    print(skill.when_lrn_mech)
            print("---------------")
