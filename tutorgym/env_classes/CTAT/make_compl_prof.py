from tutorgym.env_classes.CTAT.CTAT_tutor import CTAT_Tutor
from tutorgym.env_classes.CTAT.CTAT_problem_set import collect_CTAT_problem_sets
from tutorgym.envs.CTAT.Mathtutor.env_registry import WORKING_DOMAINS
from tutorgym.trainer import Trainer, AuthorTrainer
from tutorgym.agents.oracle_agent import OracleAgent
from tutorgym.shared import ProblemState
import random
import json


def collect_problems(domain_dirs):
    problems = []
    for domain_dir in domain_dirs:
        problem_sets = collect_CTAT_problem_sets(domain_dir)

        # print(problem_sets)
        

        for prob_set in problem_sets:
            for problem in prob_set:
                problems.append(problem)
    return problems

def make_compl_prof(self, filename, problems, problem_line_limit=50):
    """
    Generate a Completeness Profile for a list of problem configurations
    """

    profile_lines = []
    for prob_config in problems:
        if(isinstance(prob_config, tuple)):
            prob_config = self._standardize_config(*prob_config)

        self.set_problem(**prob_config)

        next_states = set([self.get_state()])#[[(,[])]]
        # next_states = [(self.get_state(),[])]
        covered_states = {ProblemState({},is_done=True)}

        has_reached_done = False
        n_problem_lines = 0

        new_states = []
        while(n_problem_lines < problem_line_limit
              and len(next_states) > 0):

            # print("N LINES:", len(profile_lines), len(covered_states))
            # print()

            # print(next_states)

            if(has_reached_done or len(new_states) == 0):
                # print("OLD", len(profile_lines), ":", len(next_states))
                state = random.choice(tuple(next_states))
                next_states.remove(state)
            else:
                # print("NEW", len(profile_lines), ":", len(next_states))
                state = random.choice(new_states)
                if(state in next_states):
                    next_states.remove(state)

            # ps = ProblemState(state)
            if(state in covered_states):
                # print("CONTINUE", state.unique_id[:5])
                continue
            else:
                covered_states.add(state)

            
            self.set_state(state)
            demos = self.get_all_demos(state)
            action_dicts = [demo.get_info() for demo in demos]
            action_hist = [a.get_info() for a in state.action_hist]
            print(state.unique_id, state.longhash[:5], f"N DEMOS: {len(demos)}")

            # for _, obj in state.objs.items():
            #     if(obj['id'] != "ProblemStatement"
            #         and 'anon' not in obj['id']
            #         # and not ('Question' in obj['id'] and len())
            #         and 'Formula' not in obj['id']
            #         and 'Unit' not in obj['id']
            #         and 'Heading' not in obj['id']
            #         and 'ctatdiv' not in obj['id']
            #         ):
            #         print(" ", obj['id'], obj.get('value', None))

            line = json.dumps({
                "problem" : self.get_problem(),
                'state' : state.objs,
                'action_hist' : action_hist,
                'correct_actions' : action_dicts,
                'incorrect_actions' : []
            })+"\n"
            profile_lines.append(line)
            n_problem_lines += 1
            # profile.write()

            new_states = []
            for demo in demos:
                # sel,_,inp = demo.sai

                self.set_state(state)
                new_state = self.apply(demo)
                
                
                if(not new_state.get_annotation("is_done", False)):
                    # print("DONE")
                    if(new_state not in covered_states):
                        if(not has_reached_done):
                            new_states.append(new_state)
                        next_states.add(new_state)
                else:
                    has_reached_done = True

                    # new_states.append((ns,hist+[(sel,inp['value'])]))


            # np.random.randint()
            # next_states = new_states
        print("PROB DONE", n_problem_lines, len(next_states))
    print("DONE", len(profile_lines))
    
    with open(filename, 'w') as profile:
        for line in profile_lines:
            profile.write(line)

if __name__ == "__main__":
    # print(len(WORKING_DOMAINS))
    # raise ValueError()

    domain_dirs = [f"../../envs/CTAT/Mathtutor/{d}/" for d in WORKING_DOMAINS]
    problems = collect_problems(domain_dirs)
    tutor = CTAT_Tutor()#demo_annotations={"src_id", "dest_id", "unique_id"})

    # if(False):
    
    # make_compl_prof(tutor, "ctat_compl.prof", problems)

    # if(False):
    for problem in problems:
        print(problem)
        tutor.set_problem(**problem)
        make_compl_prof
        agent = OracleAgent(tutor)
        trainer = Trainer(agent, tutor, problem_set=[problem], num_incorrect_force_demo=2)
    # try:
        trainer.start()

    



