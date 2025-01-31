from itertools import permutations
import numpy as np
import json
from tutorgym.utils import unique_hash
from tutorgym.shared import ProblemState, Action
import inspect
from abc import ABC, abstractmethod
from tutorgym.env_classes.env_base import TutorEnvBase

# -----------------------
# : ActionGroup


class ActionGroup:
    def __init__(self, name, actions, unordered=True, reenterable=True):
        self.name = name
        self.actions = actions
        self.unordered = unordered
        self.reenterable = reenterable

        src_ids = set()
        dest_ids = set()
        self.optional_mask = np.zeros(len(actions), dtype=np.int8)
        for i, action in enumerate(actions):
            optional = action.get_annotation("optional", False)
            self.optional_mask[i] = not optional

            src_ids.add(action.get_annotation("src_id"))
            dest_ids.add(action.get_annotation("dest_id"))

        self.out_state_ids = list(dest_ids-src_ids)


        # for action in action_group:
        #     src_ids.add(action.get_annotation("src_id"))
        #     dest_id action.get_annotation("dest_id")
            

    def __iter__(self):
        return iter(self.actions)

    def __len__(self):
        return len(self.actions)

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return self.name == other.name



# ----------------------------------------------------------------
# : StateMachineTutor Tutor

class FiniteStateMachine:
    def __init__(self, start_state, action_model):
        self.start_state = ProblemState(start_state)
        self.action_model = action_model
        self.nodes = {}
        self.groups = {}
        self._ensure_node(start_state)

    def _ensure_node(self, state):
        unique_id = state.unique_id
        if(unique_id not in self.nodes):
            self.nodes[unique_id] = {
                "state" : state,
                "edges" : {}
            }
        return self.nodes[unique_id]

    def add_edge(self, state, action, is_done=False, force_unique_id=None):
        action = Action(action) # Standardize
        state = ProblemState(state)
        node = self._ensure_node(state)

        next_state = self.action_model.apply(state, action)
        if(force_unique_id is not None):
            next_state.add_annotations({"unique_id": force_unique_id})
        
        node['edges'][action] = next_state
        self._ensure_node(next_state)
        return next_state

    def _action_group_from_list(self, action_list):
        action_list = [Action(x) for x in action_list] # Standardize
        name = "group1"
        i = 2 
        while name in self.groups:
            name = f"group{i}"
            i += 1
        return ActionGroup(name, action_list)

    def add_unordered(self, state, action_group, force_unique_id=None):
        if(isinstance(action_group, list)):
            action_group = self._action_group_from_list(action_group)
        else:
            assert action_group.name not in self.groups
        
        start_state = ProblemState(state)
        node = self._ensure_node(start_state)

        next_state = start_state.copy()
        for action in action_group:
            next_state.add_annotations({
                "group" : action_group.name,
            })
            next_state = self.action_model.apply(next_state, action)

        


        self.groups[action_group.name] = {
            "group" : action_group,
            "start_state" : start_state,
            "next_state" : next_state,
            "edges" : []
        }

        if(force_unique_id is not None):
            next_state.add_annotations({"unique_id": force_unique_id})

        node['edges'][action_group] = next_state
        self._ensure_node(next_state)
        return next_state

        # for ordered in permutations(action_list):
        #     state = start_state
        #     for action in ordered:
        #         state = self.add_edge(state, action)
        # return state # State after unordered actions

    def _group_satisfied(self, state, group):
        unfinished_actions = []
        done_mask = np.zeros(len(group), dtype=np.int8)
        for i, grp_action in enumerate(group):
            action_done = False
            for action in state.action_hist:
                if(grp_action.check(action)):
                    action_done = True
                    break

            done_mask[i] = action_done

            if(not action_done):
                unfinished_actions.append(unfinished_actions)

        is_satisfied = np.sum(done_mask | group.optional_mask) == len(group)
        return is_satisfied, unfinished_actions


    def get_next_actions(self, state):
        next_actions = None

        if(state.unique_id in self.nodes):
            out_edges = self.nodes[state.unique_id]['edges']
            next_actions = list(out_edges.keys())

        group_name = state.get_annotation("group", None)
        if(group_name in self.groups):
            # The next actions should include any unsatisfied actions
            #   in the group
            gnode = self.groups[group_name]
            group = gnode['group']
            group_satisfied, unfinished_actions = \
                self._group_satisfied(state, group)
                
            next_actions = unfinished_actions

            # If the group has been satisfied (i.e. all non-optional 
            #   actions have been taken) then any actions that leave 
            #   the group should also be included.
            if(group_satisfied):
                for out_state_id in group.out_state_ids:
                    out_edges = self.nodes[out_state_id]['edges']
                    next_actions += list(out_edges.keys())

        if(next_actions is None):
            raise ValueError(
                f"FSM given state with unrecognized unique_id {state.unique_id} " + 
                "and not annotated as part of a recognized 'group'.")

        # Skip over any optional actions and recursively add actions
        #  for the next node
        for action in [*next_actions]:
            optional = action.get_annotation("optional", False)
            a_group = action.get_annotation("group", None)
            if(optional and a_group != group_name):
                next_state = self.action_model.apply(action)
                next_actions += self.get_next_actions(next_state)

        return next_actions

    # def apply(self, state, action, make_copy=True):
    #     new_state = self.action_model.apply(state, action, make_copy=make_copy)

    #     # print(new_state)
    #     return new_state


class StateMachineTutor(TutorEnvBase):
    def __init__(self, action_model, **kwargs):
        self.action_model = action_model
        self._action_map = {}
        super().__init__(**kwargs)

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
        self.problem_config = self._standardize_config(*args, **kwargs)

        # subclasses defined fsm constructor
        self.fsm = self.create_fsm(self.start_state, **self.problem_config)
        self.set_state(self.start_state)
        # self.is_done = False
        

    def get_problem(self):
        return getattr(self, 'problem_name', self.problem_config)

    def get_problem_config(self):
        return self.problem_config

    def reset(self):
        self.state = self.start_state.copy()
        # self.is_done = False

    def get_state(self):
        return self.state

    def set_state(self, state):
        print("-- SET STATE GET NEXT -- ")
        self.state = ProblemState(state)
        self.next_actions = self.fsm.get_next_actions(state)


        for action in [*self.next_actions]:
            actor = action.get_annotation("actor", "student")
            if(actor == "tutor"):
                self.state = self.apply(action)
                break

        # print(self.next_actions)
        self._action_map = {}
        for action in self.next_actions:
            self._action_map[id(action)] = action
        # self.is_done = False

        return self.state


    def _check_w_next(self, action):
        action_addr = id(action)
        if(action_addr in self._action_map):
            return self._action_map[action_addr]

        for ca in self.next_actions:
            if(ca.check(action)): # TODO:, check_args=check_args, check_how=check_how)):
                self._action_map[action_addr] = ca
                return ca
        return None


    def check(self, action, **kwargs):
        """ Returns 1 for correct next-step Actions, -1 for incorrect ones."""
        action = Action(action) # standardize
        # correct_actions = self.fsm.get_next_actions(self.state)

        corr_action = self._check_w_next(action)
        if(corr_action is not None):
            return 1
        else:
            return -1

        # print("CHECK:", repr(action), correct_actions)
        # check_args = kwargs.get('check_args',self.check_args)
        # check_how = kwargs.get('check_how',self.check_how)
        # for ca in correct_actions:
        #     if(ca.is_equal(action, check_args=check_args, check_how=check_how)):
        #         return 1
        # return -1

    # def sai_makes_done(self, sai):
    #     return sai[0] == 'done'

    def apply(self, action, make_copy=True):
        """ Applies an Action. Modifying self.state. """

        state = self.action_model.apply(self.state, action, make_copy=make_copy)

        corr_action = self._check_w_next(action)
        dest_id = corr_action.get_annotation("dest_id", None)
        if(dest_id is not None):
            state.add_annotations({"unique_id" : dest_id})

        
        # for corr_action in self.next_actions:
        #     if(corr_action.check(action)):
        #         break


        state_group = state.get_annotation("group", None)
        action_group = action.get_annotation("group", None)
        print("corr_action_group:",  repr(corr_action))
        print("action_group:",  action_group)
        print("state_group:",  state_group)
        # if()
        # if(self.sai_makes_done(action.sai)):
        #     # self.is_done = True
        #     self.state = ProblemState({}, is_done=True)
        # else:
        #     self.state = make_next_state(self.state, action.sai)
        state = self.set_state(state)
        # self.state = state
        return state

    def _process_demo(self, action, **kwargs):
        action = Action(action.sai, 
                **{k:v for k,v in action.annotations.items() if k in self.demo_annotations
                })
        return action

    def get_demo(self, state=None, **kwargs):
        """ Returns a correct next-step Action """
        state = self.state if state is None else state
        # correct_actions = #self.fsm.get_next_actions(self.state)
        action = self.next_actions[0]
        demo = self._process_demo(action)
        self._action_map[id(demo)] = action
        return demo

    def get_all_demos(self, state=None, **kwargs):
        """ Returns all correct next-step Actions """
        state = self.state if state is None else state 
        # correct_actions = self.fsm.get_next_actions(self.state)     
        demos = []
        for action in self.next_actions:
            demo = self._process_demo(action)
            self._action_map[id(demo)] = action
            demos.append(demo)
        return demos
        # return [self._process_demo(a, **kwargs) for a in correct_actions]

    
