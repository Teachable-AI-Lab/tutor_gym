from tutorgym.shared import ProblemState
from tutorgym.env_classes.apprentice_tutor import ApprenticeTutor, HTNCognitiveModel
from shop2.domain import Task
from copy import deepcopy


class AllTutorContainer(ApprenticeTutor):
    def __init__(self, domain, problem_generator, problem_types=["power"], **kwargs):
        """
        Creates a state and sets a random problem.
        """
        super().__init__(**kwargs)        
        self.problem_types = problem_types
                
        self.domain = deepcopy(domain)        
        self.domain['solve'].preconditions = [self.domain['solve'].preconditions[0]]
        self.domain['solve'].subtasks = [self.domain['solve'].subtasks[0]]
        self.problem_generator = problem_generator
        self.set_random_problem()

    def _blank_state(self, type):
        field_params = {'x': 0, 'type': 'TextField', 'value' : "", 'width' : 100, 'height' : 50,  }
        button_params = {'x': 0, 'type': 'Button', 'width' : 100, 'height' : 50, }

        field_names = [x.name for x in self.domain['solve'].subtasks[0]]

        state: dict = { 'equation' : {'y': 10, 'locked': False,  **field_params}}
        for idx, field in enumerate(field_names):
            if field == 'done':
                state[field] = {'y': 10 + (idx + 1) * 100, **button_params}
            else:
                state[field] = {'y': 10 + (idx + 1) * 100, 'locked': False,  **field_params}

        for key, value in state.items():
            state[key]['id'] = key

        self.possible_selections = [x.name for x in self.domain['solve'].subtasks[0]]
        self.possible_args = ['equation', *self.possible_selections[:-2]]

        return ProblemState(state)                

    def set_start_state(self, initial_problem, **kwargs):
        ''' Domain implementation: Used by ApprenticeTutor.set_problem() 
            to initialize a start state.'''

        #print(args, kwargs)
        state = self._blank_state(self.problem_types)
        self.problem = initial_problem
        state['equation']['value'] = self.problem
        self.start_state = ProblemState(state)
    
    def set_random_problem(self):
        equation: str = self.problem_generator()
        self.set_problem(equation)

    def create_htn_model(self, state):
        curr_state = state.copy()
        task = [Task(head=('solve','equation'), primitive=False)]
        return HTNCognitiveModel(curr_state, task, self.domain)
    
    def get_possible_selections(self):
        return self.possible_selections

    def get_possible_args(self):
        return self.possible_args

