from tutorenvs.multicolumn_std import Action, ProblemState
from tutorenvs.utils import DataShopLogger
from colorama import Back, Fore
import colorama
from pprint import pprint
import json

class ProblemIterator:
    def __init__(self, problem_set=None, n_problems=None, **kwargs):

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
                 on_problem_end = None,
                 **kwargs):
        self.agent = agent
        self.env = env
        if(logger is None or isinstance(logger, str)):
            logger_name = logger
            if(logger_name is None):
                logger_name = type(self.env).__name__
            self.logger = DataShopLogger(logger_name, extra_kcs=['field'])
        self.always_update_state = kwargs.get('always_update_state', False)
        self.train_next_state = kwargs.get('train_next_state', False)
        self.total_incorrect = 0
        self.total_correct = 0
        self.total_hints = 0

        if('problem_set' not in kwargs and
           'n_problems' not in kwargs and 
           'outer_loop_controller' not in kwargs):
            raise ValueError("Trainer Be Given either a 'problem_set', 'n_problems', or an 'outer_loop_controller'")

        if('outer_loop_controller' in kwargs):
            self.outer_loop_controller = kwargs['outer_loop_controller']
            self.problem_iterator = self.outer_loop_controller
        else:
            self.problem_iterator = ProblemIterator(**kwargs)

        self.on_problem_end = on_problem_end

    def print_outcome(self, action, outcome_kind):
        sai = action.sai
        if(outcome_kind == "CORRECT"):
            print(Back.GREEN + Fore.BLACK  + f"CORRECT: {sai[0]} -> {sai[2]}")
        elif(outcome_kind == "INCORRECT"):            
            print(Back.RED + Fore.BLACK + f"INCORRECT: {sai[0]} -> {sai[2]}")
        elif(outcome_kind == "HINT"):
            print(Back.BLUE + Fore.YELLOW + f"HINT: {sai[0]} -> {sai[2]}")

    def tutor_train_state(self, state):
        ''' Tutor-train (i.e. train one action at a time) on 'state'.'''
        action = self.agent.act(state)
        outcome_kind = None

        if(action):
            action = Action(action) # Coax into Action Object
            reward = self.env.check(action)
            if(reward > 0):
                outcome_kind = "CORRECT"
                self.total_correct += 1
            else:
                outcome_kind = "INCORRECT"
                self.total_incorrect += 1
        else:
            action = self.env.get_demo()
            reward = 1
            outcome_kind = "HINT"
            self.total_hints += 1

        self.agent.train(state, reward=reward, 
            **action.as_train_kwargs(), # includes sai, arg_foci, etc.
             is_demo=True)

        self.print_outcome(action, outcome_kind)

        # Change the state by applying the action
        if(reward > 0 or self.always_update_state):
            self.env.apply(action)                

    def start(self):
        p = 1
        p_iter = self.problem_iterator
        for prob_args in p_iter:
            if(prob_args is None):
                prob_args = self.env.set_random_problem()
            else:
                self.env.set_problem(*prob_args)

            print(Back.WHITE + Fore.BLACK + f"STARTING PROBLEM {prob_args}")

            while(not self.env.is_done):
                state = self.env.get_state()
                self.tutor_train_state(state)

            print("+" * 100)
            print(f"Finished problem {p} of {getattr(p_iter, 'n_problems', '??')}")

            p += 1
        total = (self.total_hints+self.total_incorrect+self.total_correct)
        print(f'TOTALS  (correct:{self.total_correct}, incorrect:{self.total_incorrect}, hint:{self.total_hints}, assistance:{self.total_hints+self.total_incorrect})')
        print(f'PERCENTS(correct:{100*(self.total_correct)/total:.2f}%, incorrect:{100*(self.total_incorrect)/total:.2f}%, hint:{100*(self.total_hints)/total:.2f}%, assistance:{100*(self.total_hints+self.total_incorrect)/total:.2f}%)')

class AuthorTrainer(Trainer):
    def __init__(self, *args, **kwargs):
        super(AuthorTrainer, self).__init__(*args, **kwargs)
        self.states_trained = 0
        self.problem_jumps = 0


    def author_train_state(self, state):
        ''' Author-train (i.e. all proposed actions + available demos at once) on 'state'.'''
        actions = self.agent.act_all(state, return_kind="skill_app")
        demos = self.env.get_all_demos(state)

        # Annotate each proposed action with reward and add to training set
        train_set = []
        covered_demos = [False] * len(demos)
        for action in actions:
            # action = Action(action)
            reward = -1
            for j, demo in enumerate(demos):
                if(demo.is_equal(action, 
                    check_args=self.env.check_args,
                    check_how=self.env.check_how)):
                    reward = 1
                    covered_demos[j] = action
                    break

            print("CHECK:", reward, action, action.args)

            train_set.append({"state": state,
                              "reward" : reward,
                              **action.as_train_kwargs()})

        # Add any next demos not covered by the actions into the training set
        for i, action in enumerate(covered_demos):
            if(not action):
                demo = demos[i]
                train_set.append({"state": state,
                                  "reward" : 1,
                                  "is_demo" : True,
                                  **demo.as_train_kwargs()})

        # Apply Training Set
        self.agent.train_all(train_set)

        # Print / Log Outcomes
        for train_obj in train_set:
            outcome_kind = None
            if(not train_obj.get('is_demo',False)):
                if(train_obj['reward'] > 0):
                    outcome_kind = "CORRECT"
                    self.total_correct += 1
                else:
                    outcome_kind = "INCORRECT"
                    self.total_incorrect += 1
            else:
                outcome_kind = "HINT"
                self.total_hints += 1

            self.print_outcome(Action(train_obj['sai']), outcome_kind)

        # Change the state by applying the first demo 
        #  (or the action that covered it)
        demo = covered_demos[0]
        if(not demo):
            demo = demos[0]
        self.env.apply(demo)
        print(Back.WHITE + Fore.BLACK + f"APPLY: {demo.sai[0]} -> {demo.sai[2]}")
        return demos[1:]

    def train_prob_start_to_end(self):
        unapplied = []
        while(not self.env.is_done):
            state = self.env.get_state()
            # print("########")
            # for key, obj in state.items():
            #     print(key, obj)
            # print("########")
            unused_demos = self.author_train_state(state)
            unapplied.append((state, unused_demos))
        return unapplied

    # def train_rollout_skipped_states(self):
    #     self.env.reset()
    #     start_state = self.env.get_state()
    #     rollout = self.agent.act_rollout(start_state, json_friendly=True)
    #     print(rollout)
    #     raise ValueError()

    def train_unapplied_demo_states(self, unapplied):
        for state, demos in unapplied:            
            for demo in demos:
                self.env.set_state(state)
                self.env.apply(demo)
                state = self.env.get_state()
                self.author_train_state(state)



    def start(self):
        p_iter = self.problem_iterator
        p = 1

        problems_so_far = []
        for prob_args in p_iter:
            if(prob_args is None):
                prob_args = self.env.set_random_problem()
            else:
                self.env.set_problem(*prob_args)

            print(Back.WHITE + Fore.BLACK + f"STARTING PROBLEM {prob_args}")

            unapplied = self.train_prob_start_to_end()
            self.train_unapplied_demo_states(unapplied)

            print("+" * 100)
            print(f"Finished problem {p} of {getattr(p_iter, 'n_problems', '??')}")

            if(self.on_problem_end is not None): 
                self.on_problem_end()

            problems_so_far.append(prob_args)

            p += 1
        total = (self.total_hints+self.total_incorrect+self.total_correct)
        print(f'TOTALS  (correct:{self.total_correct}, incorrect:{self.total_incorrect}, hint:{self.total_hints}, assistance:{self.total_hints+self.total_incorrect})')
        print(f'PERCENTS(correct:{100*(self.total_correct)/total:.2f}%, incorrect:{100*(self.total_incorrect)/total:.2f}%, hint:{100*(self.total_hints)/total:.2f}%, assistance:{100*(self.total_hints+self.total_incorrect)/total:.2f}%)')
