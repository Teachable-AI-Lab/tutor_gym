import json
from tutorgym.shared import ProblemState, Action
from abc import ABC, abstractmethod

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
    def get_demo(self, state=None, **kwargs):
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
    def set_state(self, objs):
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


    def make_compl_prof(self, filename, problems):
        """
        Generate a Completeness Profile for a list of problem configurations
        """

        with open(filename, 'w') as profile:
            for prob_config in problems:
                if(isinstance(prob_config, tuple)):
                    prob_config = self._standardize_config(*prob_config)

                self.set_problem(**prob_config)
                next_states = [(self.get_state(),[])]

                covered_states = {ProblemState({})}
                while(len(next_states) > 0):
                    new_states = []
                    for state, hist in next_states:
                        ps = ProblemState(state)
                        if(ps in covered_states):
                            continue
                        else:
                            covered_states.add(ps)

                        self.set_state(state)
                        demos = self.get_all_demos(state)
                        actions = [demo.get_info() for demo in demos]
                        problem = self.get_problem()
                        profile.write(json.dumps({"problem" : problem, 'state' : state, 'hist' : hist, 'actions' : actions})+"\n")

                        for demo in demos:

                            sel,_,inp = demo.sai
                            ns = self.apply(demo)
                            
                            self.set_state(state)
                            if(not self.is_done):
                                new_states.append((ns,hist+[(sel,inp['value'])]))
                    next_states = new_states

    def make_rand_compl_prof(self, filename, num_problems=100):
        problems = []
        for i in range(num_problems):
            self.set_random_problem()
            problems.append(self.get_problem_config())
        self.make_compl_prof(filename, problems)
