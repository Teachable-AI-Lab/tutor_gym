from tutorgym.envs.apprentice_tutor.logarithms_power import LogarithmsPower
from tutorgym.trainer import AuthorTrainer
from tutorgym.utils import DataShopLogger
from tutorgym.oracle_agent import OracleAgent



logger = DataShopLogger("fractions", extra_kcs=['field'], output_dir='log_al_author')
env = LogarithmsPower(problem_types=["power"])
agent = OracleAgent(env)
# compl_evaluator = CompletenessEvaluator(eval_freq="problem_end")
trainer = AuthorTrainer(agent, env, logger=logger,
            # evaluators=[compl_evaluator],
            n_problems=20)
trainer.start()

