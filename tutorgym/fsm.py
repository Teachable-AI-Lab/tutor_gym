class State:
    def __init__(self, sai, foci=None, next=None):
        self.sai = sai
        self.foci = foci
        self.next = next # None for the final state.


class StateMachine:
    def __init__(self):
        self.cur_state = None
        self.start_state = None

    def reset(self):
        self.cur_state = self.start_state

    def apply(self, selection, action, inputs):
        if (selection == self.cur_state.sai[0]
            and action == self.cur_state.sai[1]
            and inputs['value'] == self.cur_state.sai[2]['value']):

            self.cur_state = self.cur_state.next
            return 1
        else:
            return -1

    def add_next_state(self, sai, foci=None):
        state = State(sai, foci)
        if self.start_state == None:
            self.start_state = state
        else:
            self.cur_state.next = state

        self.cur_state = state

