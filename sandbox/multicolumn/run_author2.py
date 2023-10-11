import tutorenvs
from tutorenvs.utils import DataShopLogger
from tutorenvs.multicolumn_std import MultiColumnAddition
from tutorenvs.trainer import AuthorTrainer, ProblemState
import faulthandler; faulthandler.enable()




edge_case_set = [
    ["777", "777"],
    ["773", "773"],
    ["737", "737"],
    ["377", "377"],
    ["337", "337"],
    ["733", "733"], # missing in CHI2020
    ["333", "333"], # missing in CHI2020
    ["999", "001"],
    ["999", "010"],
    ["999", "100"],
    ["999", "111"],
    ["999", "011"],
    ["999", "110"],
    ["999", "101"],
]

training_set = [
    ["534", "698"],
    ["872", "371"],
    ["839", "445"],
    ["287", "134"],
    ["643", "534"],
    ["248", "137"],
    ["234", "142"],
    ["539", "461"],
    ["433", "576"],
    ["764", "335"],
    ["533", "698"],
]

extra = [
    # ["777", "777"],
    # ["999", "101"],
    # ["999", "111"],
    # ["999", "001"],
]

def log_completeness(agent, profile='ground_truth.txt', log=[]):
    log.append(agent.eval_completeness(profile))


def run_training(agent, logger_name='MulticolumnAddition', n=10,
                 n_columns=3, author_train=True, carry_zero=False):
    logger = DataShopLogger(logger_name, extra_kcs=['field'])
    problem_set = training_set + extra + training_set   #[["777", "777"], ["666", "666"], ["777","777"]]

    env = MultiColumnAddition(check_how=False, check_args=True,
            demo_args=True, demo_how=False, n_digits=n_columns,
            carry_zero=carry_zero)
    
    trainer = AuthorTrainer(agent, env, logger=logger,
                problem_set=problem_set)#, n_problems=n)
    c_log = []
    profile = "exp_z_ground_truth.txt" if carry_zero else "ground_truth.txt"
    # profile = "leg_expz.txt"
    env.make_completeness_profile(problem_set, profile)
    trainer.on_problem_end = lambda : log_completeness(agent, profile, log=c_log)

    # else:
    #     env = MultiColumnAddition(check_how=False, check_args=False, demo_args=True, demo_how=True, n_digits=n_columns)
    #     trainer = Trainer(agent, env, logger=logger, problem_set=problem_set, n_problems=n)
    trainer.start()
    for i, obj in enumerate(c_log):
        print(f"corr={obj['correctness']*100:2.2f}%, compl={obj['completeness']*100:.2f}%")
    return c_log

from apprentice.agents.cre_agents.cre_agent import CREAgent
agent_args = {
    "search_depth" : 2,
    "where_learner": "antiunify",
    #"where_learner": "mostspecific",
    # "when_learner": "sklearndecisiontree",    
    "explanation_choice" : "least_operations",
    
    "planner" : "setchaining",
    "function_set" : ["OnesDigit","TensDigit","Add","Add3"],
    "feature_set" : [],
    #"feature_set" : ['Equals'],
    
    "extra_features" : ["SkillCandidates","Match"],
    "find_neighbors" : True,
    "when_args": {"encode_relative" : True},
}

dt_args = {
    "when_learner": "decisiontree",
    # "when_learner": "sklearndecisiontree",    
}
stand_args = {
    "when_learner": "stand",
    "which_learner": "when_prediction",
    "action_chooser" : "max_which_utility",
    "suggest_uncert_neg" : True,
}

stand_relaxed_args = {**stand_args,
    "when_args" : {
        **agent_args['when_args'],
        "split_choice" : "all_near_max"
    }
}



# import numpy as np
# import matplotlib.pyplot as plt

# markers = ['+', '.', 'o']
# def plot_cmp(d, title):
#     for i, (label, prof) in enumerate(d.items()):
        
#         cmp = [d['completeness'] for d in prof]
#         plt.plot(np.arange(1,len(cmp)+1), cmp, label=label, marker=markers[i])
#     plt.title(title)
#     plt.xlabel('Problem #')
#     plt.ylabel('Post-Problem Completeness')
#     plt.legend(loc="lower right")
#     plt.ylim(-0.05, 1.05)
#     plt.axhline(1.0, linestyle='--', color="#dddddd99")
#     plt.show()

dt_agent = CREAgent(**agent_args, **dt_args)
log_dt_cz = run_training(dt_agent)

dt_agent = CREAgent(**agent_args, **dt_args)
log_dt_cz = run_training(dt_agent)
