import json
from tutorgym.shared import ProblemState, Action
from abc import ABC, abstractmethod
import random


# ----------------------------------------------------------------
# : TutorEnvBase

class TutorEnvBase(ABC):
    def __init__(self,
                 # If should Check / Demo skill arguments 
                 demo_annotations=[],
                 check_annotations=[]):
                 # check_args=False, demo_args=False,
                 # If should Check / Demo the how-part functions 
                 # check_how=False, demo_how=False):
        self.demo_annotations = demo_annotations
        self.check_annotations = check_annotations
        self.name = type(self).__name__

    @abstractmethod
    def set_problem(self, *args, **kwargs):
        """
        Set the Tutor Environment's current problem
        """
        pass

    @abstractmethod
    def get_problem(self):
        """
        Get some kind of unique identifier for the current problem
        """
        pass
    
    @abstractmethod
    def get_problem_config(self):
        """
        Get a dictionary with the arguments used to instantiate the current problem
        """
        pass

    @abstractmethod
    def get_demo(self, state=None, **kwargs):
        """
        Get a single instance of Action for a next correct action in the Tutor
        """
        pass

    @abstractmethod
    def get_all_demos(self, state=None, **kwargs):
        """
        Get a list of instances of Action for all next correct actions in the Tutor
        """
        pass
        
    @abstractmethod
    def check(self, action, **kwargs):
        """
        Return 1 if `action` is a correct next action, otherwise return -1
        """
        pass

    @abstractmethod
    def get_state(self):
        """
        Get the current state of the Tutor
        """
        pass

    @abstractmethod
    def set_state(self, state):
        """
        Set the current state of the Tutor
        """
        pass

    @abstractmethod 
    def apply(self, action):
        """
        Apply a single action, put the Tutor in the new state and return
        the resulting state
        """
        pass

    def _standardize_config(self, *args, **kwargs):
        """
        For the *args and **kwargs of a call to set_problem, 
          convert *args and **kwargs into the equivalent joint kwargs
        """
        raise NotImplementedError()

    def get_domain_prompt(self):
        return None

    def make_compl_prof(self, filename, problems, problem_line_limit=50):
        """
        Generate a Completeness Profile for a list of problem configurations
        """
        # print("MAKE COMPL PROF", problems)
        # raise ValueError()
        profile_lines = []
        for prob_config in problems:
            if(isinstance(prob_config, tuple)):
                prob_config = self._standardize_config(*prob_config)

            self.set_problem(**prob_config)

            problem_state = self.get_state()
            next_states = set([problem_state])#[[(,[])]]
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
                    # break
                    print("OLD", len(profile_lines), ":", len(next_states))
                    state = random.choice(tuple(next_states))
                    next_states.remove(state)
                else:
                    print("NEW", len(profile_lines), ":", len(next_states))
                    state = random.choice(new_states)
                    if(state in next_states):
                        next_states.remove(state)

                # ps = ProblemState(state)
                if(state in covered_states):
                    # print("CONTINUE", state.unique_id[:5])
                    continue
                else:
                    covered_states.add(state)

                print()
                self.set_state(state)
                demos = self.get_all_demos(state)
                action_dicts = [demo.get_info() for demo in demos]
                action_hist = [a.get_info() for a in state.action_hist]
                
                print("\n".join([f"{x['id']}={x.get('value')}" for k,x in state.objs.items()]))
                # print(state.annotations)
                # print(state.unique_id, state.longhash[:5], f"N DEMOS: {len(demos)}")
                # print("HIST", len(action_hist))
                print([str(x) for x in demos])
                # print("IS EMPTY", len(demos)==0)
                if(len(demos)==0):
                    raise ValueError()

                # for demo in demos:
                #     if(demo.sai[1] == "UpdateRadioButton"):
                #         for _, obj in state.objs.items():
                #             print(" ", obj['id'], obj.get('value', None))
                            # if(obj['id'] != "ProblemStatement"
                            #     and 'anon' not in obj['id']
                            #     # and not ('Question' in obj['id'] and len())
                            #     and 'Formula' not in obj['id']
                            #     and 'Unit' not in obj['id']
                            #     and 'Heading' not in obj['id']
                            #     and 'ctatdiv' not in obj['id']
                            #     ):
                            #     print(" ", obj['id'], obj.get('value', None))
                    # print(demo.sai)

                
                line_dict = {
                    "problem" : self.get_problem(),
                    'state' : state.objs,
                    'action_hist' : action_hist,
                    'correct_actions' : action_dicts,
                    'incorrect_actions' : []
                }
                if(hasattr(self,'domain')):
                    line_dict = {
                        'domain' : self.domain,
                        **line_dict
                    }

                line = json.dumps(line_dict)+"\n"
                # print(line)
                profile_lines.append(line)
                n_problem_lines += 1
                # profile.write()

                new_states = []
                for demo in demos:
                    # sel,_,inp = demo.sai

                    self.set_state(state)
                    new_state = self.apply(demo)
                    new_state = self.get_state()
                    
                    
                    if(not new_state.get_annotation("is_done", False)):
                        # print("DONE")
                        if(new_state not in covered_states):
                            if(not has_reached_done):
                                new_states.append(new_state)
                            next_states.add(new_state)
                    else:
                        has_reached_done = True


                # np.random.randint()
                # next_states = new_states
            print("PROB DONE", n_problem_lines, len(next_states))
        print("DONE", len(profile_lines))

        # raise ValueError()
        
        with open(filename, 'w') as profile:
            for line in profile_lines:
                profile.write(line)

        
    # def make_compl_prof(self, filename, problems):
    #     """
    #     Generate a Completeness Profile for a list of problem configurations
    #     """
    #     print(problems)
    #     with open(filename, 'w') as profile:
    #         for prob_config in problems:
    #             if(isinstance(prob_config, tuple)):
    #                 prob_config = self._standardize_config(*prob_config)

    #             self.set_problem(**prob_config)
    #             next_states = [(self.get_state(),[])]

    #             covered_states = {ProblemState({})}
    #             while(len(next_states) > 0):
    #                 new_states = []
    #                 for state, hist in next_states:
    #                     print("state", state)
    #                     ps = ProblemState(state)
    #                     if(ps in covered_states):
    #                         continue
    #                     else:
    #                         covered_states.add(ps)

    #                     self.set_state(state)
    #                     demos = self.get_all_demos(state)
    #                     print("demos", demos)
    #                     actions = [demo.get_info() for demo in demos]
    #                     problem = self.get_problem()
    #                     profile.write(json.dumps({
    #                         "problem" : problem,
    #                         'state' : state.objs,
    #                         'hist' : hist,
    #                         'actions' : actions
    #                     })+"\n")

    #                     print("Shmeggo", len(demos))
    #                     for demo in demos:
    #                         print("Eggo")

    #                         sel,_,inp = demo.as_tuple()
    #                         ns = self.apply(demo)

    #                         print("ns", ns)
                            
    #                         self.set_state(state)
    #                         if(not state.get_annotation("is_done", False)):
    #                             new_states.append((ns,hist+[(sel,inp)]))
    #                 next_states = new_states

    def make_rand_compl_prof(self, filename, num_problems=100):
        problems = []
        for i in range(num_problems):
            self.set_random_problem()
            problems.append(self.get_problem_config())
        self.make_compl_prof(filename, problems)
