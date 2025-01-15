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




