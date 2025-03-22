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



        # for action in action_group:
        #     src_ids.add(action.get_annotation("src_id"))
        #     dest_id action.get_annotation("dest_id")
    @property
    def optional_mask(self):
        if(not hasattr(self, "_optional_mask")):
            self._optional_mask = np.zeros(len(self.actions), dtype=np.int8)
            for i, action in enumerate(self.actions):
                optional = action.get_annotation("optional", False)
                self._optional_mask[i] = optional
        return self._optional_mask

    @property
    def out_state_ids(self):
        if(not hasattr(self, "_out_state_ids")):
            src_ids = set()
            dest_ids = set()
            for i, action in enumerate(self.actions):
                src_ids.add(action.get_annotation("src_id"))
                dest_ids.add(action.get_annotation("dest_id"))

            # print("name:", self.name)
            # print("src_ids:", src_ids)
            # print("dest_ids:", dest_ids)
            self._out_state_ids = list(dest_ids-src_ids)
            # print("out_state_ids:", self.out_state_ids)
        return self._out_state_ids
    

    def __iter__(self):
        return iter(self.actions)

    def __len__(self):
        return len(self.actions)

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return self.name == other.name

    def __str__(self):
        return f"ActionGroup(name={self.name}, {self.actions})"

    def __repr__(self):
        return f"ActionGroup(name={self.name}, {self.actions!r})"



# ----------------------------------------------------------------
# : StateMachineTutor Tutor

class FiniteStateMachine:
    def __init__(self, start_state, action_model):
        self.start_state = ProblemState(start_state)
        self.action_model = action_model
        self.nodes = {}
        self.groups = {}
        self._ensure_node(start_state)

    # -----------------------
    # : add_edge

    def _gen_state_id(self):
        i = len(self.nodes)+1
        name = str(i)
        while name in self.nodes:
            i += 1
            name = str(i)
        
        # print("DID GENERATE STATE ID", name)
        return name

    def _ensure_node(self, state, back_up_id=None):
        unique_id = state.get_annotation("unique_id")
        # print("UB", unique_id, back_up_id)
        if(unique_id is None):
            unique_id = back_up_id if back_up_id else self._gen_state_id()
            # print("DID GENERATE STATE ID", unique_id)
            state.add_annotations({"unique_id" : unique_id})
        # else:
            # print("DID HAVE STATE ID", unique_id)

        if(unique_id not in self.nodes):
            self.nodes[unique_id] = {
                "state" : state,
                "edges" : {}
            }
        return self.nodes[unique_id]

    def add_edge(self, state, action, is_done=False, force_unique_id=None):
        
        action = Action(action) # Standardize
        _state = ProblemState(state)
        src_node = self._ensure_node(_state)

        state_id = _state.get_annotation("unique_id")
        src_id = action.get_annotation('src_id', state_id)
        # assert state_id == src_id, f"state's unique_id={state_id!r} does not agree with action src_id={src_id!r}"
        action.add_annotations({"src_id" : src_id})

        next_state = self.action_model.apply(_state, action, make_copy=True)

        if(force_unique_id is not None):
            dest_id = force_unique_id
        else:
            dest_id = action.get_annotation('dest_id')

        dest_node = self._ensure_node(next_state, dest_id)
        next_id = next_state.get_annotation("unique_id", dest_id)
        if(dest_id is None):
            dest_id = next_id

        # dest_id = action.get_annotation('dest_id', next_id)
        assert next_id == dest_id, f"state's unique_id={next_id!r} does not agree with action dest_id={dest_id!r}"
        action.add_annotations({"dest_id" : dest_id})
        next_state.add_annotations({'unique_id' : dest_id})


        src_node['edges'][action] = next_state

        # print(f"-- add_edge({src_id}, {dest_id})", repr(action), "\n")
        
        return next_state

    # -----------------------
    # : add_unordered

    def _gen_action_group_name(self):
        # action_list = [Action(x) for x in action_list] # Standardize
        name = "group1"
        i = 2 
        while name in self.groups:
            name = f"group{i}"
            i += 1
        return name
        # return ActionGroup(name, action_list)

    def _node_add_group(self, node, group_name):
        groups = node.get('groups', set())
        groups.add(group_name)
        # print(id(groups))
        node['groups'] = groups

    def _format_group(self, action_group):
        # inp_actions = [Action(x) for x in action_group] # Standardize
        if(isinstance(action_group, ActionGroup)):
            name = action_group.name
        else:
            name = self._gen_action_group_name()  

        # Copy actions and ensure annotated with group name
        actions = []
        for action in action_group:
            action_copy = Action(action)
            action_copy.add_annotations({"group" : name})
            actions.append(action_copy)
        return ActionGroup(name, actions)

    def add_unordered(self, state, action_group, force_unique_id=None):
        

        # if(isinstance(action_group, list)):
        #     action_group = self._action_group_from_list(action_group)

        action_group = self._format_group(action_group)

        if(action_group.name in self.groups):
            return self.groups[action_group.name]['next_state']
        # else:
        #     assert action_group.name not in self.groups
        
        start_state = ProblemState(state)#.copy()
        state_id = start_id = start_state.get_annotation("unique_id")
        node = self._ensure_node(start_state, state_id)
            
        # print("state_id", start_state.annotations)
        _state = start_state
        
        for i, action in enumerate(action_group):
            state_id = _state.get_annotation("unique_id")
            src_id = action.get_annotation('src_id', state_id)
            # assert state_id == src_id, f"state's unique_id={state_id!r} does not agree with action src_id={src_id!r}"
            action.add_annotations({"src_id": src_id})

            src_node = self._ensure_node(_state, src_id)
            _state.add_annotations({
                "groups" : set([action_group.name]),
            })

            # print("_node_add_group", src_id, action_group.name)
            self._node_add_group(src_node, action_group.name)
            next_state = self.action_model.apply(_state, action)
            
            if(force_unique_id is not None and i == len(action_group)-1):
                dest_id = force_unique_id
            else:
                dest_id = action.get_annotation('dest_id')

            dest_node = self._ensure_node(next_state, dest_id)
            next_id = next_state.get_annotation("unique_id")

            dest_id = action.get_annotation('dest_id', next_id)
            assert next_id == dest_id, f"state's unique_id={next_id!r} does not agree with action dest_id={dest_id!r}"
            action.add_annotations({"dest_id" : dest_id})

            _state = next_state

        
        # if(force_unique_id):
        #     # print("FORCE NEXT", force_unique_id, next_id)
        #     assert force_unique_id == dest_id
        #     _state.add_annotations({'unique_id' : dest_id})
        _state.add_annotations({"groups" : set([action_group.name])})


        # next_state.add_annotations({
        #     "groups" : [action_group.name],
        #     "unique_id" : action.get_annotation('src_id')
        # })
        # node = self._ensure_node(next_state)
        # self._add_group(node, action_group.name)


        self.groups[action_group.name] = {
            "group" : action_group,
            "start_state" : start_state,
            "next_state" : _state,
            "edges" : []
        }

        if(force_unique_id is not None):
            _state.add_annotations({"unique_id": force_unique_id})

        # node['edges'][action_group] = next_state
        # self._ensure_node(next_state)


        # print(f"-- add_unordered {action_group.name}({start_id},{next_id})", len(action_group), "\n")
        # print(f"state_annotations", start_state.annotations, _state.annotations)
        return _state

        # for ordered in permutations(action_list):
        #     state = start_state
        #     for action in ordered:
        #         state = self.add_edge(state, action)
        # return state # State after unordered actions

    # ---------------------
    # : get_next_actions

    def _action_satisfied(self, state, action):
        # print("Looking for", action)
        for hist_action in state.action_hist:
            # print("\tH", hist_action)
            if(action.check(state, hist_action)):
                # print("\t::", action, hist_action)
                return True
                # action_done = True
                # break
        return False


    def _group_satisfied(self, state, group):
        unfinished_actions = []
        done_mask = np.zeros(len(group), dtype=np.int8)

        # print(group.optional_mask)
        for i, grp_action in enumerate(group):
            # prefix = "* " if group.optional_mask[i] else "  "
            # print(f"{prefix}grp_action", i, ":", grp_action)
            action_done = self._action_satisfied(state, grp_action)

            # for action in state.action_hist:
            #     # print(action, grp_action)
            #     if(grp_action.check(state, action)):
            #         action_done = True
            #         break

            done_mask[i] = action_done

            if(not action_done):
                unfinished_actions.append(grp_action)

        is_satisfied = np.sum(done_mask | group.optional_mask) == len(group)
        return is_satisfied, unfinished_actions


    def get_next_actions(self, state):
        # print("get_next_actions STATE", state.unique_id)

        next_actions = None
        state_id = state.get_annotation("unique_id")
        node = self.nodes.get(state_id, None)
        state_groups = state.get_annotation("groups", None)
        # print("gna group_name", state_id, state_groups)

        if(state_groups is None and node is not None):
            state_groups = node['state'].get_annotation("groups", None)

        # print("gna group_name", state_id, state_groups)
        # print("Node", node)

        all_groups_satisfied = True
        exit_actions = []
        next_actions = []
        if(state_groups is not None):# and 
            # print(' -- groups', state_groups)
            # any(gn in self.groups for gn in node['groups'])):
            for group_name in state_groups:
                # The next actions should include any unsatisfied actions
                #   in the group
                gnode = self.groups[group_name]
                group = gnode['group']
                group_satisfied, unfinished_actions = \
                    self._group_satisfied(state, group)
                
                # print("unfinished_actions", unfinished_actions)
                next_actions += unfinished_actions

                # If the group has been satisfied (i.e. all non-optional 
                #   actions have been taken) then any actions that leave 
                #   the group should also be included.
                if(group_satisfied):
                    
                    for out_state_id in group.out_state_ids:
                        out_edges = self.nodes[out_state_id]['edges']
                        exit_actions += list(out_edges.keys())
                    # print("GROUP SATISFIED!", group.out_state_ids, list(out_edges.keys()))
                else:
                    all_groups_satisfied = False

        # print("all_groups_satisfied", all_groups_satisfied, state.unique_id in self.nodes)
        if(all_groups_satisfied and state.unique_id in self.nodes):
            # print(' -- edges', len(node['edges']))
            out_edges = node['edges']
            exit_actions += list(out_edges.keys())

        # print("n_exit_actions", len(exit_actions))
        for exit_action in exit_actions:
            satisfied = self._action_satisfied(state, exit_action)
            # print("exit_action", exit_action, f"id={exit_action.get_annotation('unique_id')} ({exit_action.get_annotation('src_id')}, {exit_action.get_annotation('dest_id')})", satisfied)
            if(not satisfied):
                next_actions.append(exit_action)    

        
            # for na in next_actions:
            #     if(na.sai[0] == "recombine"):
            #         print("<<", na)
                    # raise ValueError()

        if(next_actions is None):
            raise ValueError(
                f"FSM given state with unrecognized unique_id {state.unique_id} " + 
                "and not annotated as part of a recognized 'group'.")

        # Skip over any optional actions and recursively add actions
        #  for the next node
        # TODO: Not sure if this is correct"
        if(False):
            for action in [*next_actions]:
                # print(action)
                optional = action.get_annotation("optional", False)
                a_group = action.get_annotation("group", None)
                if(optional and a_group != group_name):
                    next_state = self.action_model.apply(action)
                    next_actions += self.get_next_actions(next_state)


        # print("next_actions", len(next_actions))        
        actions_sorted = sorted(next_actions, key=lambda x : x.get_annotation("optional", False))

        # print("actions_sorted", len(actions_sorted))
        return actions_sorted

    def apply(self, state, action, make_copy=True):
        new_state = self.action_model.apply(state, action, make_copy=make_copy)

        # print(new_state)
        return new_state


class StateMachineTutor(TutorEnvBase):
    def __init__(self, action_model, **kwargs):
        self.action_model = action_model
        self._action_map = {}
        self.next_action_filters = kwargs.get("next_action_filters", [])
        super().__init__(**kwargs)

    def action_is_done(self, action):
        raise NotImplementedError("Subclass must implement action_is_done().")

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
        # print(args, kwargs)
        self.set_start_state(*args, **kwargs)

        # print("self.start_state", self.start_state)
        # self.start_state = ProblemState(self.start_state)
        self.problem_config = self._standardize_config(*args, **kwargs)

        # print("BEF annotations:", self.start_state.annotations)
        # subclasses defined fsm constructor
        self.fsm = self.create_fsm(self.start_state, **self.problem_config)

        # print("AFT annotations:", self.start_state.annotations)
        if(self.start_state.get_annotation("unique_id") is None):
            self.start_state.add_annotations({"unique_id" : "1"})

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
        # print("-- SET STATE GET NEXT -- ")
        self.state = ProblemState(state)

        # print("annotations:", self.state.annotations)

        # No need to handle next actions if done
        if(self.state.get_annotation("is_done", False) == True):
            self.next_actions = []
            return self.state

        self.next_actions = self.fsm.get_next_actions(state)

        for nfilter in self.next_action_filters:
            self.next_actions = nfilter(self.next_actions)

        # print("\nNext Actions")
        # for a in self.next_actions:
        #     prefix = "* " if a.get_annotation("optional", False) else "  "
        #     print(prefix, a)

        for action in [*self.next_actions]:
            actor = action.get_annotation("actor", "student")
            if(actor == "tutor"):
                # print("Tutor Performed:", action)
                self.state = self.apply(action)
                return self.state
                # break

        # print(self.next_actions)
        groups = set()
        self._action_map = {}
        for action in self.next_actions:
            group = action.get_annotation("group", None)
            if(group is not None and group not in groups):
                groups.add(group)
                
            self._action_map[id(action)] = action
        # self.is_done = False
        self.state.add_annotations({"groups" : groups})
        # print("GROUPS", groups)

        return self.state


    def _check_w_next(self, action):
        action_addr = id(action)
        if(action_addr in self._action_map):
            return self._action_map[action_addr]

        for ca in self.next_actions:
            if(ca.check(self.state, action)): # TODO:, check_args=check_args, check_how=check_how)):
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

        corr_action = self._check_w_next(action)


        # TODO: There is difference in how groups are added or removed 
        #  from the state which depends on whether the state graph is 
        #  unordered. 
        


        if(self.action_is_done(action)):
            state = ProblemState({}, is_done=True)
        else:
            state = self.action_model.apply(self.state, action, make_copy=make_copy)
        
        dest_id = corr_action.get_annotation("dest_id", None)
        if(dest_id is not None):
            state.add_annotations({"unique_id" : dest_id})

        # NOTE: This messes things up because the last group action can
        #  cause the state to leave the group
        # groups = self.state.get_annotation("groups", set())
        # group = corr_action.get_annotation("group", None)
        # if(group is not None):
        #     groups.add(group)
        # state.add_annotations({"groups" : groups})        

        

        # for corr_action in self.next_actions:
        #     if(corr_action.check(action)):
        #         break


        # state_group = state.get_annotation("group", None)
        # action_group = action.get_annotation("group", None)
        # print("corr_action_group:",  repr(corr_action))
        # print("action_group:",  action_group)
        # print("state_group:",  state_group)
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
        action = Action(action.as_tuple(), 
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

        print(demos)
        return demos
        # return [self._process_demo(a, **kwargs) for a in correct_actions]

    
