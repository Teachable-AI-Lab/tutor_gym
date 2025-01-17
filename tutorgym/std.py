
from itertools import permutations
from apprentice.shared import SAI
import numpy as np
import json
from tutorgym.utils import unique_hash
import inspect

# ----------------------------------
# : ProblemState

class ProblemState:
    # Global factory for MemSet Objects (w/ defualt context)
    # ms_builder = MemSetBuilder()

    def __new__(cls, objs):
        if(isinstance(objs, ProblemState)):
            return objs
        self = super().__new__(cls)
        self.objs = objs
        # self.memset = ms_builder(objs)
        # self._uid = f"S_{self.memset.long_hash()}"
        return self

    def __getitem__(self, attr):
        return self.objs[attr]

    def __setitem__(self, attr, val):
        if(self.objs.get(attr,None) != val):
            self._uid = None #Invalidate uid on change
        self.objs[attr] = val

    def copy(self):
        objs_copy = {k : {**v} for k,v in self.objs.items()}
        ps = ProblemState(objs_copy)
        return ps

    def __copy__(self):
        return self.copy()

    @property
    def uid(self):
        if(getattr(self, '_uid', None) is None):
            # Note: Slow-ish way to update modifications via rebuilding
            # self.memset = self.ms_builder(self.objs)
            sorted_state = sorted(self.objs.items())
            self._uid = self._uid = f"S_{unique_hash(sorted_state)}"
        return self._uid
        

    def __eq__(self, other):
        # NOTE: uids long/hash-conflict safe so this should be fine
        return self.uid == other.uid

    def __hash__(self):
        return hash(self.uid)

    def __str__(self):
        return self.uid[:8]

    def __repr__(self):
        return self.uid[:8]

# ----------------------------------
# : Action


action_translator_registry = {} 
def register_action_translator(_type):
    ''' Register a function for translating a user defined action
        type into a standard Action. 
    
    Example Usage:
        @register_action_translator(MyCustomActionType)
        def my_translator(my_obj):
            sai = (my_obj.selection, my_obj.action_type, my_obj.inputs) 
            return Action(sai, args=my_obj.args)
    '''
    def wrapper(func):
        action_translator_registry[_type] = func        
        return func

    return wrapper


annotation_equal_registry = {} 
def register_annotation_equal(anno_name):
    ''' Register a special __equal__ implementation for a
        particular annotation kind. 

        Example Usage
        @register_annotation_equal("args")
        def unordered_equals(args1, args2):
            ...
            return sorted(args1) == sorted(args2)
    '''

    def wrapper(func):
        annotation_equal_registry[anno_name] = func
        return func
    return wrapper



def _standardize_action(inp): 
    if(isinstance(inp, (list,tuple))):
        selection, action_type, inputs = inp
        annotations = {}
    elif(isinstance(inp, dict)):
        selection = inp['selection']
        action_type = inp.get('action_type', inp.get('action'))
        if(action_type is None):
            raise KeyError("'action_type' | 'action'")
        inputs = inp['inputs']
        annotations = {k:v for k,v in inp.items() if k not in ("selection", "action_type", "action", "inputs")}

    elif(hasattr(inp, 'selection')):
        selection = inp.selection
        action_type = getattr(inp, 'action_type', None)
        if(action_type is None):
            action_type = getattr(inp, 'action', None)
        inputs = inp.inputs

        annotations = {k:v for k,v in inp.__dict__.items() if k not in ("selection", "action_type", "action", "inputs")}
    else:
        raise ValueError(f"Unable to translate {inp} to Action.")

    return (selection, action_type, inputs), annotations


class Action:
    ''' An object representing the ideal action taken by an agent.
        Includes Selection-ActionType-Inputs (SAI) and optional annotations 
        like the string of the how-part of the skill that produced the SAI
        and the arguments it used to produce the action.
    '''
    def __new__(cls, sai, **annotations):        
        # If get an Action then make a copy
        if(isinstance(sai, Action)):
            self = super().__new__(cls)
            self.sai = sai.sai
            self.annotations = {**sai.annotations, **annotations}
        
        else:
            # If get a type with an action translator then make from that
            translator = action_translator_registry.get(type(sai), None)
            if(translator):
                # print("TRANSLATE!", sai)
                self = translator(sai)
                self.annotations = {**self.annotations, **annotations}
                # print("AANNO!?", self.annotations)

            else:
                self = super().__new__(cls)
                self.sai, obj_annos = _standardize_action(sai)
                self.annotations = {**obj_annos, **annotations}


        return self

    def is_equal(self, other, check_annotations=[]):        
        if(self.sai != other.sai):
            return False

        for anno in check_annotations:
            self_has = anno in self.annotations
            other_has = anno in other.annotations
            # print("has", self_has, other_has)
            if(self_has != other_has):
                return False

            if(not self_has):
                continue

            self_anno = self.annotations[anno]
            other_anno = other.annotations[anno]

            eq = annotation_equal_registry.get(anno, None)

            if(eq is not None):
                if(not eq(self_anno, other_anno)):
                    return False
            else:
                if(self_anno != other_anno):
                    return False

        return True        

    def __eq__(self, other):
        return self.is_equal(other)

    def __hash__(self):
        return hash((unique_hash(self.sai), unique_hash(self.annotations)))

    def __str__(self):
        return f"{self.sai[0]}->{self.sai[2]['value']}"

    def __repr__(self):
        s = f"{self.sai[1]}({self.sai[0]}, {self.sai[2]}"

        for anno_name, anno in self.annotations.items():
            s += f", {anno_name}={anno}"
        return s + ")"

    def copy(self, omit_annotations=[]):
        sai = self.sai
        # args = self.args if not omit_args else None
        # how_str = self.how_str if not omit_how else None
        new_annos = {k:v for k,v in self.annotations.items() if k not in omit_annotations}
        return Action(sai, **new_annos)

    def __copy__(self):
        return self.copy()

    def as_train_kwargs(self):
        return {
            "sai" : self.sai,
            **self.annotations,
            }

    def get_info(self):
        return {
            "selection" : self.sai[0],
            "action_type" : self.sai[1],
            "inputs" : self.sai[2],
            **self.annotations,
        }


# TODO: Should reuse the predict_next_state() machinery in cre_agent 
#  to implement this.
def make_next_state(state, sai):
    next_state = state.copy()
    selection, action_type, inputs = sai
    if(action_type == "UpdateTextField"):
        next_state[selection]['value'] = inputs['value']
        next_state[selection]['locked'] = True        
    return next_state

# ----------------------------------
# : FiniteStateMachine

class FiniteStateMachine:
    def __init__(self, start_state):
        self.start_state = ProblemState(start_state)
        self.nodes = {}
        self._ensure_node(start_state)

    def _ensure_node(self, state):
        if(state not in self.nodes):
            self.nodes[state] = {
                "state" : state,
                "edges" : {}
            }
        return self.nodes[state]

    def add_edge(self, state, action, is_done=False):
        action = Action(action) # Standardize
        state = ProblemState(state)
        node = self._ensure_node(state)
        if(is_done):
            next_state = ProblemState({})
        else:
            next_state = make_next_state(state, action.sai)
        node['edges'][action] = next_state
        self._ensure_node(next_state)
        return next_state

    def add_unordered(self, state, action_list):
        action_list = [Action(x) for x in action_list] # Standardize
        start_state = ProblemState(state)
        for ordered in permutations(action_list):
            state = start_state
            for action in ordered:
                state = self.add_edge(state, action)
        return state # State after unordered actions

    def get_next_actions(self, state):
        out_edges = self.nodes[state]['edges']
        return list(out_edges.keys())

    # def copy(self, omit_action_parts=[]):
    #     new_fsm = FiniteStateMachine(self.start_state)
    #     for state, node in new_fsm.nodes.items():
    #         new_node = new_fsm._ensure_node(state)
    #         new_edges = {}
    #         for action, next_state in node['edges'].items():
    #             action_copy = action.copy(omit_action_parts)
    #             new_edges[action_copy] = next_state
    #         new_node['edges'] = new_edges
    #         new_fsm.nodes[state] = new_node
    #     return new_fsm


class TutorEnvBase:
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
        

def load_fsm(file_path):
    ''' Load a finite state machine from a brd or json file.'''
    raise NotImplementedError


class StateMachineTutor(TutorEnvBase):
    def create_fsm(self):
        raise NotImplementedError("Subclass must implement create_fsm().")
            
    def set_start_state(self, *args, **kwargs):
        raise NotImplementedError("Subclass must implement set_start_state().")

    def _standardize_config(self, *args, **kwargs):
        sig = inspect.signature(self.set_start_state)

        problem_config = {}
        for (arg_name, arg) in zip(sig.parameters, args):
            problem_config[arg_name] = arg

        return {**problem_config, **kwargs}

    def set_problem(self, *args, **kwargs):
        # subclasses defined start state
        self.set_start_state(*args, **kwargs)
        # subclasses defined fsm constructor
        self.fsm = self.create_fsm(self.start_state)
        self.state = self.start_state
        self.is_done = False

        self.problem_config = self._standardize_config(*args, **kwargs)
        

    def get_problem(self):
        return getattr(self, 'problem_name', self.problem_config)

    def get_problem_config(self):
        return self.problem_config

    def reset(self):
        self.state = self.start_state.copy()
        self.is_done = False

    def get_state(self):
        return self.state.objs

    def set_state(self, objs):
        self.state = ProblemState(objs)
        self.is_done = False

    def check(self, action, **kwargs):
        """ Returns 1 for correct next-step Actions, -1 for incorrect ones."""
        action = Action(action) # standardize
        correct_actions = self.fsm.get_next_actions(self.state)

        # print("CHECK:", repr(action), correct_actions)
        check_args = kwargs.get('check_args',self.check_args)
        check_how = kwargs.get('check_how',self.check_how)
        for ca in correct_actions:
            if(ca.is_equal(action, check_args=check_args, check_how=check_how)):
                return 1
        return -1

    def sai_makes_done(self, sai):
        return sai.selection == 'done'

    def _action_to_sai(self, action):
        if(not isinstance(action, (SAI, tuple, list, dict))):
            if(hasattr(action, 'sai')):
                sai = SAI(*action.sai)
            else:
                raise ValueError(f"Action {action} does not have .sai property.")
        else:
            sai = SAI(action)
        return sai

    def apply(self, action):
        """ Applies an Action. Modifying self.state. """
        sai = self._action_to_sai(action)
        if(self.sai_makes_done(sai)):
            self.is_done = True
            self.state = ProblemState({})
        else:
            self.state = make_next_state(self.state, sai)
        return self.state.objs

    def _process_demo(self, action, **kwargs):
        # demo_args = kwargs.get('demo_args',self.demo_args)
        # demo_how = kwargs.get('demo_how',self.demo_how)
        # print("PROCESS", demo_how, demo_args)
        # if(not demo_args or not demo_how):
        action = Action(action.sai, 
                **{k:v for k,v in action.annotations.items() if k in self.demo_annotations
                })
        # action = action.copy(ommit_annotations=not demo_args, omit_how=not demo_how)
        return action

    def get_demo(self, state=None, **kwargs):
        """ Returns a correct next-step Action """
        state = self.state if state is None else state
        correct_actions = self.fsm.get_next_actions(self.state)
        return self._process_demo(correct_actions[0],**kwargs)

    def get_all_demos(self, state=None, **kwargs):
        """ Returns all correct next-step Actions """
        state = self.state if state is None else state 
        correct_actions = self.fsm.get_next_actions(self.state)
        print("DEMOS:")
        for a in correct_actions:
            print('\t', repr(a))
        return [self._process_demo(a, **kwargs) for a in correct_actions]

    def make_compl_prof(self, filename, problems):
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
