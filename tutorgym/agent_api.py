from abc import ABC, abstractmethod

class AbstactAgent(ABC):
    @abstractmethod
    def train(self, state, action, reward, 
              is_demo=False, is_start=False, **kwargs):
        """
        Train the agent on a single learning opportunity.
        
        Args:
        state: Current state
            action: Action taken
            reward: Reward received 
        """
        pass

    @abstractmethod
    def train_all(self, training_set, states={}, **kwargs):
        """
        Train the agent on a list of dicts of key-word arguments to train()
        
        Args:
            training_set: List of dicts of keyword arguments to train()
            states: optionally states can be provided as {unique_state_id : state_dict}
                     and the argument in each training_set item can just be a unique_state_id
                     string instead of a whole state object. This can cut down on how much
                     data needs to be sent over the network in cases where it is reasonable
                     for the agent to have states indexed in it's episodic memory.
        """
        pass

    @abstractmethod
    def act(self, state, **kwargs):
        """
        Produce an action for a single state.
        
        Args:
            state: Current state
        
        Returns:
            Produced action
        """
        pass

    @abstractmethod 
    def act_all(self, state, **kwargs):
        """
        Return all predicted correct next actions for a state
        
        Args:
            state: Current state
            
        Returns:
            List of selected actions
        """
        pass
