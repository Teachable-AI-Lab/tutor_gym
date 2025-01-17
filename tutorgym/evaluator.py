import os
from tutorgym.std import Action

def _load_profile_line(line):
    import json
    item = json.loads(line)
    profile_actions = [Action(x) for x in item['actions']]
    state = item['state']
    is_start = len(item['hist'])==0

    # if(hasattr(agent, "standardize_state")):
    #     state = self.standardize_state(state)
        
    return state, item, profile_actions

class ProfileIterator:
    def __init__(self, profile):
        self.profile = profile

        if(isinstance(profile, str)):
            self.profile_list = []
            with open(profile, 'r') as profile_f:
                for line_ind, line in enumerate(profile_f):
                    state, item, profile_actions = _load_profile_line(line)
                    profile_actions = [Action(p_act) for p_act in profile_actions]
                    self.profile_list.append((state, item, profile_actions))
        elif(isinstance(profile, list)):
            self.profile_list = profile 

    def __iter__(self):
        return iter(self.profile_list)

def eval_completeness(agent, compl_prof, verbosity=1, partial_credit=False,
                        print_diff=True, print_correct=False, return_diffs=False,
                        check_annotations=[],
                        **kwargs):
    ''' Evaluates an agent's correctness and completeness against a completeness profile.'''
    import json, os
    if(verbosity > 0):
        print("--START EVAL COMPLETENESS--")

    profile_iter = compl_prof
    if(not isinstance(compl_prof, ProfileIterator)):
        profile_iter = ProfileIterator(compl_prof)
        
    n_correct, total = 0, 0
    n_first_correct, total_states = 0, 0
    diffs = []
    for state, item, profile_actions in profile_iter:
        is_start = len(item['hist'])==0

        prob_uid = None
        if(hasattr(agent, "standardize_state")):
            state = agent.standardize_state(state)
            prob_uid = state.get("__uid__")

        agent_actions = agent.act_all(state, return_kind='skill_app',
         is_start=is_start, prob_uid=prob_uid, eval_mode=True)

        conv_agent_actions = [Action(a_act) for a_act in agent_actions]

        # Find the difference of the sets
        cov = [False]*len(profile_actions)
        correct = []
        extra = []
        first_correct = False
        for j, a_act in enumerate(conv_agent_actions):
            is_correct = False
            for i, p_act in enumerate(profile_actions):
                if(not cov[i] and 
                   a_act.is_equal(p_act, check_annotations)):
                    cov[i] = is_correct = True
                    break
            if(is_correct):
                correct.append(a_act.get_info())
                if(j == 0):
                    first_correct = True
            else:
                extra.append(a_act.get_info())
        missing = [p_act for i, p_act in enumerate(profile_actions) if cov[i]]


        # set_agent_actions = set(agent_actions)
        # set_profile_actions = set(profile_actions)
        # missing = set_profile_actions - set_agent_actions
        # extra = set_agent_actions - set_profile_actions
        # correct = set_agent_actions.intersection(set_profile_actions)
        n_diff = len(missing) + len(extra)

        # print("AGENT:", conv_agent_actions)
        # print("PROFILE:", profile_actions)
        # print("-", missing)
        # print("+", extra)
        # print("=", correct)
        # print()

        diffs.append({"problem": item['problem'], 'hist' : item['hist'], "-": list(missing),"+": list(extra), "=" : list(correct)})

        if(partial_credit):
            total += len(set_profile_actions)
            n_correct += max(0, len(set_profile_actions)-n_diff)
        else:
            total += 1
            n_correct += n_diff == 0

        total_states += 1
        if(first_correct):
            n_first_correct += 1

    if(print_diff):
        for diff in diffs:
            n_diffs = len(diff['-']) + len(diff['+'])
            
            continue

            if(n_diffs != 0):
                print(f"--DIFF: {diff['problem']} {diff['hist']} --")
                for m in diff['-']:
                    print("  -", m.sai[0], m.sai[2]['value'])
                for m in diff['+']:
                    print("  +", m.sai[0], m.sai[2]['value'])
            if(print_correct == True or 
               print_correct=="if_diff" and n_diffs > 0):
                for m in diff['=']:
                    print("  =", m.sai[0], m.sai[2]['value'])    

    completeness = n_correct / total
    correctness = n_first_correct / total_states

    if(verbosity > 0):
        print(f"Correctness : {correctness*100:.2f}%",print_diff)
        print(f"Completeness : {completeness*100:.2f}%")
    out = {"completeness" : completeness, "correctness" : correctness}

    if(return_diffs):
        out['diffs'] = diffs

    print(out)
    return out


class CompletenessEvaluator:
    def __init__(self, name="CompletenessEval", eval_freq="problem_end",
            compl_prof=None, verbosity=1,
            print_skills=False, print_htn=False,
            print_diff=True, print_correct="if_diff",
            check_annotations=None):

        self.name = name
        self.eval_freq = eval_freq
        self.compl_prof = compl_prof
        self.print_skills = print_skills
        self.print_htn = print_htn
        self.print_diff = print_diff
        self.print_correct = print_correct
        self.log = []
        self.verbosity = verbosity
        self.check_annotations = check_annotations

    def initialize(self, trainer, agent, env):
        self.trainer = trainer
        self.agent = agent
        self.env = env

        # Ensure that a ground-truth completeness profile exists
        if(self.compl_prof is None):
            self.compl_prof = f'.{type(self.env).__name__}_rand100.compl_prof'
            if(not os.path.exists(self.compl_prof)):
                if(self.verbosity > 0):
                    print("-- No completeness profile specified." +
                          f"Generating new profile at {self.compl_prof}. --")

                self.env.make_rand_compl_prof(
                    self.compl_prof, num_problems=100)
            else:
                if(self.verbosity > 0):
                    print(f"-- Using completeness profile: {self.compl_prof}.")
                          
        assert os.path.exists(self.compl_prof), \
            f"No such completeness profile {self.compl_prof}."

        self.profile_iter = ProfileIterator(self.compl_prof)

        if(self.check_annotations is None):
            self.check_annotations = self.env.check_annotations


    def do_eval(self, context_data={}):
        '''
        Called by the trainer. Runs step of evaluation according to evaluator's eval_freq 
        ("step_end", "problem_end", "train_end", etc.)
        '''
        completeness_data = eval_completeness(self.agent, 
            self.profile_iter, verbosity=self.verbosity,
            print_diff=self.print_diff, print_correct=self.print_correct,
            check_annotations=self.check_annotations
        )

        self.log.append({
            "step_num" : len(self.log),
            **context_data, **completeness_data
        })

        if(self.print_skills or self.print_htn):
            print("---------------")
            if(self.print_htn):
                print(self.agent.process_lrn_mech.grammar)
                
            if(self.print_skills):
                for skill in agent.skills.values():
                    print()
                    print(skill)
                    print(skill.when_lrn_mech)
            print("---------------")
