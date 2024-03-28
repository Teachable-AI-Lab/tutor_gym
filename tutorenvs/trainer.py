from tutorenvs.multicolumn_std import Action, ProblemState
from tutorenvs.utils import DataShopLogger
from colorama import Back, Fore, Style
import colorama
from colorama import init
from pprint import pprint
import json

# init(autoreset=True)

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
                 act_return_kind = "sai",
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
        self.always_update_state = kwargs.get('always_update_state', False)
        self.train_next_state = kwargs.get('train_next_state', False)
        self.total_incorrect = 0
        self.total_correct = 0
        self.total_hints = 0
        self.act_return_kind = act_return_kind

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


    def _to_train_kwargs(self, state, action, reward, is_demo=False, is_start=None):
        if(self.act_return_kind == "skill_app" and not is_demo):
            return {"state" : state,
                    "skill_app" : action,
                    "is_start" : is_start,
                    "reward" : reward}
        else:
            return {"state" : state,
                    "reward" : reward,
                    "is_start" : is_start,
                    **action.as_train_kwargs(),
                    "is_demo" : is_demo}

    def print_outcome(self, action, outcome_kind):
        extra = ""
        
        if(isinstance(action, Action)):
            sai = action.sai
            arg_str = ','.join(action.args) if action.args else "???"
            extra = f"{getattr(action,'how_str', '??')}({arg_str})"
        elif('sai' in action):
            sai = Action(action['sai']).sai
            # print(action)
            arg_foci = action.get('arg_foci',['???'])
            if(arg_foci is None):
                arg_foci = ['???']
            extra = f"{getattr(action,'how_str','???')}({','.join(arg_foci)})"
        elif('skill_app' in action):
            skill_app = action['skill_app']
            sai = Action(skill_app.sai).sai        
            extra = f'{skill_app.__repr__(add_sai=False)}'
            # how_part = getattr(getattr(skill_app,'skill'),'how_part', "???")
            # arg_foci = getattr(skill_app,'arg_foci',['???'])
            # print("arg_foci", arg_foci)
            # if(arg_foci is None):
            #     arg_foci = []
            # extra = f"{how_part}({','.join(arg_foci)})"

        if(outcome_kind == "CORRECT"):
            print(Back.GREEN + Fore.BLACK  + f"CORRECT: {sai[0]} -> {sai[2]} {extra}" + Style.RESET_ALL)
        elif(outcome_kind == "INCORRECT"):            
            print(Back.RED + Fore.BLACK + f"INCORRECT: {sai[0]} -> {sai[2]} {extra}" + Style.RESET_ALL)
        elif(outcome_kind == "HINT"):
            print(Back.BLUE + Fore.YELLOW + f"HINT: {sai[0]} -> {sai[2]} {extra}" + Style.RESET_ALL)

    def tutor_train_state(self, state, is_start=False):
        ''' Tutor-train (i.e. train one action at a time) on 'state'.'''
        action = self.agent.act(state, return_kind=self.act_return_kind,
            is_start=is_start)
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

        action_kwargs = action.as_train_kwargs()
        s,a,i = action_kwargs['sai']
        self.logger.log_step(s, a, i['value'], outcome_kind, step_name=s, kcs=[s])

        self.agent.train(
            **self._to_train_kwargs(state, action, reward, 
             is_start=is_start,
             is_demo=outcome_kind=="HINT")
        )
        self.print_outcome(action, outcome_kind)

        # Change the state by applying the action
        if(reward > 0 or self.always_update_state):
            self.env.apply(action)

        return reward                

    def start(self):
        self.logger.set_student()
        p = 1
        p_iter = self.problem_iterator
        for prob_args in p_iter:
            if(prob_args is None):
                prob_args = self.env.set_random_problem()
            else:
                self.env.set_problem(*prob_args)
            self.logger.set_problem(self.env.problem_name)

            print(Back.WHITE + Fore.BLACK + f"STARTING PROBLEM {self.env.problem_name}"  + Style.RESET_ALL)

            is_start = True
            while(not self.env.is_done):
                state = self.env.get_state()
                rew = self.tutor_train_state(state, is_start=is_start)
                if(rew > 0):
                    is_start = False

            print("+" * 100)
            print(f"Finished problem {p} of {getattr(p_iter, 'n_problems', '??')}")

            p += 1
        total = (self.total_hints+self.total_incorrect+self.total_correct)
        print(f'TOTALS  (correct:{self.total_correct}, incorrect:{self.total_incorrect}, hint:{self.total_hints}, assistance:{self.total_hints+self.total_incorrect})')
        print(f'PERCENTS(correct:{100*(self.total_correct)/total:.2f}%, incorrect:{100*(self.total_incorrect)/total:.2f}%, hint:{100*(self.total_hints)/total:.2f}%, assistance:{100*(self.total_hints+self.total_incorrect)/total:.2f}%)')

class AuthorTrainer(Trainer):
    def __init__(self, *args, **kwargs):
        # Author trainer defaults return kind to 'skill_app'
        kwargs['act_return_kind'] = kwargs.get('act_return_kind', 'skill_app')
        super(AuthorTrainer, self).__init__(*args, **kwargs)
        self.states_trained = 0
        self.problem_jumps = 0


    def author_train_state(self, state, is_start=None):
        ''' Author-train (i.e. all proposed actions + available demos at once) on 'state'.'''
        actions = self.agent.act_all(state, is_start=is_start,
            return_kind=self.act_return_kind)
        demos = self.env.get_all_demos(state)

        # print("ACTIONS")
        # for action in actions:
        #     print(action)

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

            # print("CHECK:", reward, action, action.args)

            train_set.append(self._to_train_kwargs(state, action, reward, is_start=is_start))
                
        # Add any next demos not covered by the actions into the training set
        for i, action in enumerate(covered_demos):
            if(not action):
                train_set.append(
                    self._to_train_kwargs(state, demos[i], 
                        reward=1, is_demo=True, is_start=is_start)
                )

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

            self.print_outcome(train_obj, outcome_kind)

        # Change the state by applying the first demo 
        #  (or the action that covered it)
        demo = covered_demos[0]
        if(not demo):
            demo = demos[0]
        self.env.apply(demo)
        print(Back.WHITE + Fore.BLACK + f"APPLY: {demo.sai[0]} -> {demo.sai[2]}" + Style.RESET_ALL)
        return demos[1:]

    def train_prob_start_to_end(self):

        is_start = True
        unapplied = []

        
        while(not self.env.is_done):
            state = self.env.get_state()
            # print("########")
            # for key, obj in state.items():
            #     print(key, obj)
            # print("########")
            unused_demos = self.author_train_state(state, is_start)
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
            if(prob_args is None):
                prob_args = self.env.set_random_problem()
            else:
                self.env.set_problem(*prob_args)

            problem = getattr(self.env, 'problem_name', self.env.problem_config)
            print(Back.WHITE + Fore.BLACK + f"STARTING PROBLEM {problem}" + Style.RESET_ALL)

            # print("START ROLLOUT")
            # state = self.env.get_state()
            # self.agent.act_rollout(state, is_start=True)
            # print("END ROLLOUT")

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
