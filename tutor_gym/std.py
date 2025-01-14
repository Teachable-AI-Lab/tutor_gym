import hashlib
from base64 import b64encode
from itertools import permutations
from apprentice.shared import SAI
import numpy as np
import json

# ----------------------------------
# : ProblemState

def update_unique_hash(m,obj):
    if(isinstance(obj,str)):
        m.update(obj.encode('utf-8'))
    elif(isinstance(obj,(tuple,list, np.ndarray))):
        for i,x in enumerate(obj):
            update_unique_hash(m,i)
            update_unique_hash(m,x)
    elif(isinstance(obj,dict)):
        for k,v in obj.items():
            update_unique_hash(m,k)
            update_unique_hash(m,v)
    elif(isinstance(obj,bytes)):
        m.update(obj)
    else:
        m.update(str(obj).encode('utf-8'))


def unique_hash(stuff, hash_func='sha256'):
    '''Returns a 64-bit encoded hashstring of some 'stuff' '''
    m = hashlib.new(hash_func)
    update_unique_hash(m,stuff) 

    # Encode in base64 map the usual altchars '/' and "+' to 'A' and 'B".
    s = b64encode(m.digest(),altchars=b'AB').decode('utf-8')
    # Strip the trailing '='.
    s = s[:-1]
    return s



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

class Action:
    ''' An object representing the ideal action taken by an agent.
        Includes Selection-ActionType-Inputs (SAI) and optional annotations 
        like the string of the how-part of the skill that produced the SAI
        and the arguments it used to produce the action.
    '''
    def __init__(self, sai, args=None, how_str=None):

        # If first input is an Action, then copy it 
        if(isinstance(sai, Action)):
            self.sai = sai.sai
            self.args = sai.args if args is None else args
            self.how_str = sai.how_str if how_str is None else how_str
        # Otherwise fill in a new one
        else:
            # if(hasattr(sai,'sai')):
            #     self.sai = SAI(sai.sai) # standardize
                
            # else:
            if(isinstance(sai, SAI)):
                # Always make a copy from as_tuple() to standardize
                # and avoid side effects from reusing the same object
                sai = sai.as_tuple()
            self.sai = SAI(sai)
            self.args = args
            self.how_str = how_str

        if args is not None:        
            self.args = tuple(args)

    def is_equal(self, other, check_args=False, check_how=False):
        # Whatever 'other' is it must have an sai property 
        #  or be an convertable to an SAI.
        self_sai = self.sai
        other_only_sai = False
        if(hasattr(other, 'sai')):
            other_sai = SAI(other.sai)
        elif(isinstance(other, (SAI, tuple, dict, list))):
            other_sai = SAI(other)
            other_only_sai = True
        else:
            return False        

        if(self_sai != other_sai):
            return False

        # If Action has args then check that
        if(check_args and self.args is not None and not other_only_sai):
            # print("DO CHECK ARGS")
            other_args = getattr(other,'args', None)
            if(other_args is None and hasattr(other, "match")):
                other_args = other.match[1:]
            if(other_args is None):
                return False

            sorted_self_args = sorted(self.args)
            sorted_other_args = sorted([x if isinstance(x,str) else x.id for x in other_args])
            if(sorted_self_args != sorted_other_args):
                # print("Args NOT EQ")
                return False

        # If Action has how_str then check that
        if(check_how and self.how_str is not None and not other_only_sai):
            # print("DO CHECK HOW")
            other_how_str = getattr(other, 'how_str', None)
            if(other_how_str is None):
                other_skill = getattr(other, 'skill', None)
                other_func = getattr(other_skill, 'how_part', None)
                other_how_str = str(other_func) 
            if(self.how_str != other_how_str):
                # print("Func Not Equal")
                return False

        return True        

    def __eq__(self, other):
        return self.is_equal(self, other)

    def __hash__(self):
        return hash((self.sai, self.args, self.how_str))

    def __str__(self):
        return f"{self.sai.selection}->{self.sai.inputs['value']}"

    def __repr__(self):
        s = f"{self.sai.action_type}({self.sai.selection}, {self.sai.inputs}"
        if(self.args is not None):
            s += f", args={self.args}"
        if(self.how_str is not None):
            s += f", how_str={self.how_str!r}"
        return s + ")"

    def copy(self, omit_args=False, omit_how=False):
        sai = self.sai
        args = self.args if not omit_args else None
        how_str = self.how_str if not omit_how else None
        return Action(sai, args, how_str)

    def __copy__(self):
        return self.copy()

    def as_train_kwargs(self):
        return {
            "sai" : self.sai,
            "arg_foci" : self.args,
                # TODO: Need good way of signaling how_str to agent.  
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
                 check_args=False, demo_args=False,
                 # If should Check / Demo the how-part functions 
                 check_how=False, demo_how=False):
        self.check_args = check_args
        self.demo_args = demo_args
        self.check_how = check_how
        self.demo_how = demo_how
        self.name = type(self).__name__
        

def load_fsm(file_path):
    ''' Load a finite state machine from a brd or json file.'''
    raise NotImplementedError


class StateMachineTutor(TutorEnvBase):
    def create_fsm(self):
        raise NotImplementedError("Subclass must implement create_fsm().")
            
    def set_start_state(self, *args, **kwargs):
        raise NotImplemented

    def set_problem(self, *args, **kwargs):
        # Any StateMachineTutor can load a brd
        if(len(args)== 1 and isinstance(args[0], (str, FiniteStateMachine))):
            fsm = args[0]
            if(isinstance(fsm, str)):
                fsm = load_fsm(fsm)
            self.fsm = fsm
            self.state = self.start_state = fsm.start_state

        # Or a subclass can implement set_start_state() and create_fsm() 
        #  which take custom arguments the particular domain.
        else:
            # subclasses defined start state
            self.set_start_state(*args, **kwargs)
            # subclasses defined fsm constructor
            self.fsm = self.create_fsm(self.start_state)
            self.state = self.start_state
        self.is_done = False
        self.problem_config = (args, kwargs)

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
        demo_args = kwargs.get('demo_args',self.demo_args)
        demo_how = kwargs.get('demo_how',self.demo_how)
        # print("PROCESS", demo_how, demo_args)
        # if(not demo_args or not demo_how):
        action = action.copy(omit_args=not demo_args, omit_how=not demo_how)
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
        # print("DEMOS:")
        # for a in correct_actions:
        #     print('\t', repr(a))
        return [self._process_demo(a, **kwargs) for a in correct_actions]

    def make_completeness_profile(self, problems, output_file):
        with open(output_file, 'w') as profile:
            for prob_args in problems:
                self.set_problem(*prob_args)
                next_states = [(self.get_state(),[])]

                covered_states = set()
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
                        sais = [d.sai.get_info() for d in demos]
                        problem = getattr(self, 'problem_name', self.problem_config)
                        profile.write(json.dumps({"problem" : problem, 'state' : state, 'hist' : hist, 'sais' : sais})+"\n")

                        for d in demos:
                            sel,_,inp = d.sai
                            ns = self.apply(d)
                            
                            self.set_state(state)
                            if(not self.is_done):
                                new_states.append((ns,hist+[(sel,inp['value'])]))
                    next_states = new_states

