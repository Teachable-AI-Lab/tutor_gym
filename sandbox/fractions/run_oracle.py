from tutorgym.env_classes.misc.fraction_arith.fractions import FractionArithmetic
from tutorgym.trainer import Trainer, AuthorTrainer
from tutorgym.evaluator import CompletenessEvaluator
from tutorgym.utils import DataShopLogger
from tutorgym.utils import compare
from tutorgym.agents.oracle_agent import OracleAgent
from tutorgym.shared import Action



logger = DataShopLogger("fractions", extra_kcs=['field'], output_dir='log_al_author')
env = FractionArithmetic(problem_types=["AD"], n_fracs=2)
# env = FractionArithmetic(problem_types=["AD","AS","M"], n_fracs=2)
agent = OracleAgent(env)
# compl_evaluator = CompletenessEvaluator(eval_freq="problem_end")

env.set_problem(op='+', fracs=[(1,3),(1,2)])

if(False):
    print("----------_")

    state = env.apply(Action("check_convert", "UpdateTextField", "x"))
    # print("action_hist", state.action_hist)

    print(">>", [d.get_annotation("group") for d in env.next_actions])
    print()

    state = env.apply(Action("conv_num2", "UpdateTextField", "3"))

    print(">>", [d.get_annotation("group") for d in env.next_actions])
# print(">>", len(env.get_all_demos()))
# print("action_hist", state.action_hist)

# env.set_problem(op='+', fracs=[(1,3),(1,2)])
# env.apply(Action("conv_den1", "UpdateTextField", "12"))
# print(env.get_all_demos())

trainer = AuthorTrainer(agent, env, logger=logger,
            # evaluators=[compl_evaluator],
            n_problems=1)
trainer.start()

