from tutorgym.shared import Action
import numpy as np

class OracleAgent:
    def __init__(self, env):
        self.env = env

    def act(self, state, **kwargs):
        demo = self.env.get_demo(state)
        return demo

    def act_all(self, state, **kwargs):
        demos = self.env.get_all_demos(state)
        return demos

    def train(self, state, action, reward, 
              is_demo=False, is_start=False, **kwargs):
        pass

    def train_all(self, training_set, states={}, **kwargs):
        pass


def logit(x):
    return np.log(x) - np.log(1 -x)

def inv_logit(x):
    return 1. / (1. + np.exp(-x))

class RandomOracleAgent:
    def __init__(self, env, start_prob=.3, 
                correct_learn_rate=.05,
                incorrect_learn_rate=.025):
        self.env = env
        self.correct_log_odds = logit(start_prob)
        self.correct_learn_rate = correct_learn_rate
        self.incorrect_learn_rate = incorrect_learn_rate

    def flip_correct(self):
        p = inv_logit(self.correct_log_odds)
        return np.random.choice([0,1], p=[1.0-p, p])
    
    def act(self, state, **kwargs):
        demo = self.env.get_demo(state)
        if(self.flip_correct()):
            return demo
        else:
            sel, act, inp = demo.as_tuple()
            return Action((sel, act, {"value": "wrong"}))
        return demo

    def act_all(self, state, **kwargs):
        demos = self.env.get_all_demos(state)
        return demos

    def train(self, state, action, reward, 
              is_demo=False, is_start=False, **kwargs):
        if(reward > 0):
            self.correct_log_odds += self.correct_learn_rate
        else:
            self.correct_log_odds += self.incorrect_learn_rate
        print("TRAIN", self.correct_log_odds)

    def train_all(self, training_set, states={}, **kwargs):
        pass



