from tutorgym.envs.fraction_arithmetic.fractions_std import FractionArithmetic
from tutorgym.trainer import Trainer, AuthorTrainer
from tutorgym.evaluator import CompletenessEvaluator
from tutorgym.utils import DataShopLogger
from tutorgym.utils import compare
from tutorgym.oracle_agent import OracleAgent



logger = DataShopLogger("fractions", extra_kcs=['field'], output_dir='log_al_author')
env = FractionArithmetic(problem_types=["AD","AS","M"], n_fracs=2)
agent = OracleAgent(env)
# compl_evaluator = CompletenessEvaluator(eval_freq="problem_end")
trainer = AuthorTrainer(agent, env, logger=logger,
            # evaluators=[compl_evaluator],
            n_problems=20)
trainer.start()

