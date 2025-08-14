from tutorgym.shared import Action, ProblemState
from tutorgym.utils import DataShopLogger
from colorama import Back, Fore, Style
import colorama
from colorama import init
from pprint import pprint
import json

# init(autoreset=True)

class ProblemIterator:
    def __init__(self, problem_set=None, n_problems=None, **kwargs):
        # print("problem_set", problem_set)
        # raise ValueError()
        if(problem_set is not None):
            n_problems = 0 if n_problems is None else n_problems
            self.n_problems = max(n_problems, len(problem_set))
            self.problem_set = problem_set
        else:   
            self.n_problems = n_problems
            self.problem_set = []

        self.p = 0

    def __iter__(self):
        return self

    def __next__(self):
        p = self.p
        if(p >= self.n_problems):
            raise StopIteration
        self.p += 1
        if(p < len(self.problem_set)):
            prob_args = self.problem_set[p]
            return prob_args
        else:
            return None

class Trainer:
    def __init__(self, agent, env, logger=None,
                 num_incorrect_force_demo=-1,
                 evaluators=[],
                 problem_end_callbacks = [],
                 step_end_callbacks = [],
                 train_end_callbacks = [],
                 agent_action_repr = "action",
                 agent_state_repr = "obj_dicts",
                 **kwargs):
        self.agent = agent
        self.env = env
        if(logger is None or isinstance(logger, str)):
            logger_name = logger
            if(logger_name is None):
                logger_name = type(self.env).__name__
            self.logger = DataShopLogger(logger_name, extra_kcs=['field'])
        else:
            self.logger = logger
        self.num_incorrect_force_demo = num_incorrect_force_demo
        self.always_update_state = kwargs.get('always_update_state', False)
        self.train_next_state = kwargs.get('train_next_state', False)
        self.total_incorrect = 0
        self.total_correct = 0
        self.total_hints = 0
        self.agent_action_repr = agent_action_repr
        self.agent_state_repr = agent_state_repr

        if('problem_set' not in kwargs and
           'n_problems' not in kwargs and 
           'outer_loop_controller' not in kwargs):
            raise ValueError("Trainer Be Given either a 'problem_set', 'n_problems', or an 'outer_loop_controller'")

        if('outer_loop_controller' in kwargs):
            self.outer_loop_controller = kwargs['outer_loop_controller']
            self.problem_iterator = self.outer_loop_controller
        else:
            self.problem_iterator = ProblemIterator(**kwargs)

        self.step_end_evaluators = []
        self.problem_end_evaluators = []
        self.train_end_evaluators = []

        for ev in evaluators:
            ev.initialize(self, agent, env)
            if(ev.eval_freq == "step_end"):
                self.step_end_evaluators.append(ev)
            elif(ev.eval_freq == "problem_end"):
                self.problem_end_evaluators.append(ev)
            elif(ev.eval_freq == "train_end"):
                self.train_end_evaluators.append(ev)
            else:
                raise ValueError(f"Unrecognized eval_freq: {ev.eval_freq}.")

        self.problem_end_callbacks = problem_end_callbacks
        self.step_end_callbacks = step_end_callbacks
        self.train_end_callbacks = train_end_callbacks


    def _state_to_kwargs(self, state, is_start=None):
        if(self.agent_state_repr == "obj_dicts"):
            s = {"state" : state.objs, **state.annotations, "is_start" : is_start,}
        else:
            s = {"state" : state, "is_start" : is_start}
        return s

    def _to_train_kwargs(self, state, action, reward, is_demo=False, is_start=None):

        s = self._state_to_kwargs(state, is_start)

        if(isinstance(action, Action)):
            a = {"action" : action,
                 **action.annotations}
        else:
            a = {"action" : action}

        # if(self.agent_action_repr == "skill_app" and not is_demo):
        #     print("A")
            
        # elif(self.agent_action_repr == "action"):
        #     print("B", self.agent_action_repr)
        #     a = {"action" : action,
        #          **action.annotations}
        # else:
        #     print("C")
        #     a = action.as_train_kwargs()

        d = {**s, 
            **a,
            "reward": reward,
            "is_demo" : is_demo
            }
        # if('how_str' in d):
        #     d['how_help'] = d.get('how_str', None)

        return d
        # # if(self.agent_action_repr == "skill_app" and not is_demo):
        #     return {"state" : state,
        #             "skill_app" : action,
        #             "is_start" : is_start,
        #             "reward" : reward}
        # # else:
        #     return {"state" : state,
        #             "reward" : reward,
        #             "is_start" : is_start,
        #             **action.as_train_kwargs(),
        #             "is_demo" : is_demo}

    def print_outcome(self, action, outcome_kind):
        extra = ""
        
        if(isinstance(action, Action)):
            sel, at, inp = action.as_tuple()
            extra = ','.join([f"{k}={v}" for k,v in action.annotations.items()])
        # elif('sai' in action):
        #     sai = Action(action['sai']).as_tuple()
        #     # print(action)
        #     arg_foci = action.get('arg_foci',['???'])
        #     if(arg_foci is None):
        #         arg_foci = ['???']
        #     extra = f"{getattr(action,'how_str','???')}({','.join(arg_foci)})"
        # elif('skill_app' in action):
        #     print("ACTION", action)
        #     skill_app = action['skill_app']
        #     sai = Action(skill_app.sai).as_tuple()        
        #     extra = f'{skill_app.__repr__(add_sai=False)}'
            # how_part = getattr(getattr(skill_app,'skill'),'how_part', "???")
            # arg_foci = getattr(skill_app,'arg_foci',['???'])
            # print("arg_foci", arg_foci)
            # if(arg_foci is None):
            #     arg_foci = []
            # extra = f"{how_part}({','.join(arg_foci)})"

        if(outcome_kind == "CORRECT"):
            print(Back.GREEN + Fore.BLACK  + f"CORRECT: {sel} -> {inp} {extra}" + Style.RESET_ALL)
        elif(outcome_kind == "INCORRECT"):            
            print(Back.RED + Fore.BLACK + f"INCORRECT: {sel} -> {inp} {extra}" + Style.RESET_ALL)
        elif(outcome_kind == "HINT"):
            print(Back.BLUE + Fore.YELLOW + f"HINT: {sel} -> {inp} {extra}" + Style.RESET_ALL)

    def tutor_train_state(self, state, is_start=False, force_demo=False):
        ''' Tutor-train (i.e. train one action at a time) on 'state'.'''

        if(not force_demo):
            # actions = self.agent.act_all(
            action = self.agent.act(**self._state_to_kwargs(state, is_start),
                return_kind=self.agent_action_repr)
        else:
            action = None

        
        outcome_kind = None

        if(action):
            conv_action = Action(action)
            reward = self.env.check(conv_action)
            if(reward > 0):
                outcome_kind = "CORRECT"
                self.total_correct += 1
            else:
                outcome_kind = "INCORRECT"
                self.total_incorrect += 1
        else:
            action = self.env.get_demo()
            conv_action = Action(action)
            reward = 1
            outcome_kind = "HINT"
            self.total_hints += 1

        # print("A ACTION:", action)

        s,a,inp = action.as_tuple()
        self.logger.log_step(s, a, inp, outcome_kind, step_name=s, kcs=[s])

        self.agent.train(
            **self._to_train_kwargs(state, action, reward, 
             is_start=is_start,
             is_demo=outcome_kind=="HINT")
        )
        self.print_outcome(conv_action, outcome_kind)

        # Change the state by applying the action
        if(reward > 0 or self.always_update_state):
            self.env.apply(conv_action)

        return reward                

    def start(self):
        self.logger.set_student()
        p = 1
        p_iter = self.problem_iterator
        for prob_args in p_iter:
            if(prob_args is None):
                prob_args = self.env.set_random_problem()
            else:
                self.env.set_problem(**prob_args)
            self.logger.set_problem(self.env.problem_name)

            print(Back.WHITE + Fore.BLACK + f"STARTING PROBLEM {self.env.problem_name}"  + Style.RESET_ALL)

            is_start = True
            incorr_streak = 0
            while True:#(not self.env.is_done):
                state = self.env.get_state()
                if(state.get_annotation("is_done") == True):
                    break

                force_demo = False
                if(self.num_incorrect_force_demo >= 0 and 
                   incorr_streak >= self.num_incorrect_force_demo):
                    force_demo = True
                
                rew = self.tutor_train_state(state, is_start=is_start, force_demo=force_demo)
                if(rew > 0):
                    incorr_streak = 0
                    is_start = False
                else:
                    incorr_streak += 1

            print("+" * 100)
            print(f"Finished problem {p} of {getattr(p_iter, 'n_problems', '??')}")

            p += 1
        total = (self.total_hints+self.total_incorrect+self.total_correct)
        print(f'TOTALS  (correct:{self.total_correct}, incorrect:{self.total_incorrect}, hint:{self.total_hints}, assistance:{self.total_hints+self.total_incorrect})')
        print(f'PERCENTS(correct:{100*(self.total_correct)/total:.2f}%, incorrect:{100*(self.total_incorrect)/total:.2f}%, hint:{100*(self.total_hints)/total:.2f}%, assistance:{100*(self.total_hints+self.total_incorrect)/total:.2f}%)')

class AuthorTrainer(Trainer):
    def __init__(self, *args, **kwargs):
        # Author trainer defaults return kind to 'skill_app'
        kwargs['agent_action_repr'] = kwargs.get('agent_action_repr', 'action')
        super(AuthorTrainer, self).__init__(*args, **kwargs)
        self.states_trained = 0
        self.problem_jumps = 0

    def author_train_state(self, state, is_start=None):
        ''' Author-train (i.e. all proposed actions + available demos at once) on 'state'.'''
        actions = self.agent.act_all(**self._state_to_kwargs(state, is_start), #, is_start=is_start,
            return_kind=self.agent_action_repr)
        demos = self.env.get_all_demos(state)

        # print("demos:", len(demos))
        # for demo in demos:
        #     print(demo)

        # print("actions:", len(actions))
        # for action in actions:
        #     print(action)

        # print("state: ")
        # for k,v in state.items():
        #     print("[L]" if v.get('locked',False) else "[ ]", k, v.get('value',""))

        # Annotate each proposed action with reward and add to training set
        train_set = []
        covered_demos = [False] * len(demos)
        for action in actions:
            conv_action = Action(action)
            reward = -1
            for j, demo in enumerate(demos):
                if(demo.is_equal(conv_action,
                    check_annotations=self.env.check_annotations
                    )):

                    reward = 1
                    covered_demos[j] = action
                    break

            train_set.append(self._to_train_kwargs(state, action, reward, is_start=is_start))

            if(reward == 1):
                self.print_outcome(conv_action, "CORRECT")
                self.total_correct += 1
            else:
                self.print_outcome(conv_action, "INCORRECT")
                self.total_incorrect += 1
                
        # Add any next demos not covered by the actions into the training set
        for i, action in enumerate(covered_demos):
            if(not action):
                self.print_outcome(demos[i], "HINT")
                self.total_hints += 1
                train_set.append(
                    self._to_train_kwargs(state, demos[i], 
                        reward=1, is_demo=True, is_start=is_start)
                )

        # print("train_set", train_set)

        # Apply Training Set
        self.agent.train_all(train_set)

        
        # Change the state by applying the first demo 
        #  (or the action that covered it)
        demo = covered_demos[0]
        if(not demo):
            demo = demos[0]
        # self.env.apply(demo)
        print(Back.WHITE + Fore.BLACK + f"APPLY: {demo.selection} -> {demo.input}" + Style.RESET_ALL)
        return demos#[1:]

    def train_prob_start_to_end(self):

        is_start = True
        unapplied = []

        
        while True:#(not self.env.is_done):
            state = self.env.get_state()
            if(state.get_annotation("is_done") == True):
                break
            # print("########")
            # for key, obj in state.items():
            #     print(key, obj)
            # print("########")
            demos = self.author_train_state(state, is_start)
            unapplied.append((state, unused_demos))
            is_start = False
        return unapplied

    # def train_rollout_skipped_states(self):
    #     self.env.reset()
    #     start_state = self.env.get_state()
    #     rollout = self.agent.act_rollout(start_state, json_friendly=True)
    #     print(rollout)
    #     raise ValueError()

    def train_unapplied_demo_states(self, unapplied):
        for state, demos in unapplied:
            orig_state = state
            for demo in demos:
                self.env.set_state(orig_state)
                self.env.apply(demo)
                state = self.env.get_state()
                self.author_train_state(state)


    def start(self):
        p_iter = self.problem_iterator
        p = 1

        problems_so_far = []
        for prob_args in p_iter:
            print("P ITER", prob_args)
            if(prob_args is None):
                prob_args = self.env.set_random_problem()
            else:
                self.env.set_problem(**prob_args)

            problem = getattr(self.env, 'problem_name', self.env.problem_config)
            print(Back.WHITE + Fore.BLACK + f"STARTING PROBLEM {problem}" + Style.RESET_ALL)

            
            # Begin with the start state
            states = [self.env.get_state()]
            cov = set([str(states[0])])
            is_start = True

            while len(states) > 0:
                new_states = []

                # Go through all states
                for state in states:
                    # Train on state
                    self.env.set_state(state)
                    demos = self.author_train_state(state, is_start)

                    callback_context = {
                        "trainer": self, 
                        "problem_num" : p, "problem" : problem
                        # TODO: Some kind of state info
                    }
                    for ev in self.step_end_evaluators:
                        ev.do_eval(callback_context)
                    for callback in self.step_end_callbacks:
                        callback(callback_context);

                    # Follow the states after the next correct actions
                    for demo in demos:
                        self.env.set_state(state)
                        self.env.apply(demo)
                        n_state = self.env.get_state()

                        # Don't bother repeating states
                        s_str = str(n_state)
                        if(s_str in cov or 
                           n_state.get_annotation("is_done") == True):
                            continue
                        else:
                            cov.add(s_str)

                        new_states.append(n_state)
                states = new_states
                is_start = False

            print("L_COV:", len(cov))

                    
                #     for demo in demos:
                #         # Prep State after demo
                #         self.env.set_state(orig_state)
                #         self.env.apply(demo)

                #         # Don't bother repeating states
                #         aft_state = self.env.get_state()
                #         a_str = str(aft_state)
                #         if(a_str in cov):
                #             continue
                #         cov.add(a_str)

                #         # Train from state after demo to end
                #         # NOTE: there will be some redundancy (should fix?)
                #         st_unapp = self.train_prob_start_to_end()
                #         for s,d in st_unapp:
                #             if(str(s) not in cov):
                #                 new_unapp.append((s,d))

                #     cov.add(s_str)
                # unapplied = new_unapp

            print("+" * 100)
            print(f"Finished problem {p} of {getattr(p_iter, 'n_problems', '??')}")
                
            problems_so_far.append(prob_args)

            callback_context = {"trainer": self, "problem_num" : p, "problem" : problem}
            for ev in self.problem_end_evaluators:
                ev.do_eval(callback_context)
            for callback in self.problem_end_callbacks:
                callback(callback_context);

            p += 1
        total = (self.total_hints+self.total_incorrect+self.total_correct)
        print(f'TOTALS  (correct:{self.total_correct}, incorrect:{self.total_incorrect}, hint:{self.total_hints}, assistance:{self.total_hints+self.total_incorrect})')
        print(f'PERCENTS(correct:{100*(self.total_correct)/total:.2f}%, incorrect:{100*(self.total_incorrect)/total:.2f}%, hint:{100*(self.total_hints)/total:.2f}%, assistance:{100*(self.total_hints+self.total_incorrect)/total:.2f}%)')

        callback_context = {"trainer": self}
        for ev in self.train_end_evaluators:
            ev.do_eval(callback_context)
        for callback in self.train_end_callbacks:
            callback(callback_context);
