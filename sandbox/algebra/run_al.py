from tutorenvs.algebra_std import Algebra
from tutorenvs.utils import DataShopLogger
from tutorenvs.trainer import Trainer
from colorama import Back, Fore
import colorama
from pprint import pprint
from cre.utils import PrintElapse
colorama.init(autoreset=True)

# Domain specific prior knowledge  
# with PrintElapse("import funcs"):
from algebra_funcs import (GetOperand, GetOperator, ReverseSign, ExprVar, EvalArithmetic,
    AddTerm, SubTerm, DivTerm, MulTerm, ExprConst,ExprCoeff, ExprDenCoeff, 
    WriteMultiply, WriteDivide, WriteSubtract, WriteAdd, Numerator, Denominator)
# raise ValueError()



def run_training(agent, logger_name='Algebra', n=10,
                 n_rows=3, author_train=True):
    
    logger = DataShopLogger(logger_name, extra_kcs=['field'], output_dir='log_al')
    env = Algebra(demo_args=True, demo_how=False, n_rows=n_rows,
                  var_denoms=True)

    trainer = Trainer(agent, env, 
        # problem_set=[('777','777')],
        logger=logger,  n_problems=n)
    trainer.start()


if __name__ == "__main__":
    import faulthandler; faulthandler.enable()

    import numpy as np
    np.set_printoptions(edgeitems=30, linewidth=100000, 
        formatter=dict(float=lambda x: "%.3g" % x))

    
    import sys, argparse
    parser = argparse.ArgumentParser(
        description='Runs AL agents on algebra')
    parser.add_argument('--n-agents', default=50, type=int, metavar="<n_agents>",
                        dest="n_agents", help="number of agents")
    parser.add_argument('--n-problems', default=500, type=int, metavar="<n_problems>",
                        dest="n_problems", help="number of problems")
    parser.add_argument('--n-rows', default=3, type=int, metavar="<n_rows>",
                        dest="n_rows", help="number of rows")
    parser.add_argument('--agent-type', default='DIPL',metavar="<agent_type>",
                        dest="agent_type", help="type of agents DIPL or RHS_LHS")

    args = parser.parse_args(sys.argv[1:])

    logger_name = f'mc_addition_{args.agent_type}_{args.n_rows}col_{args.n_problems}probs'
    for _ in range(args.n_agents):

        if(args.agent_type.upper() == "DIPL"):   
            from apprentice.agents.cre_agents.cre_agent import CREAgent         
            agent_args = {
                "search_depth" : 2,
                # "where_learner": "antiunify",
                "where_learner": "mostspecific",
                # "where_learner": "generalize",
                
                # "when_learner": "sklearndecisiontree",
                "when_learner": "decisiontree",
                                
                # For STAND
                # "when_learner": "stand",
                # "which_learner": "when_prediction",
                # "action_chooser" : "max_which_utility",
                # "suggest_uncert_neg" : True,

                # "explanation_choice" : "least_operations",
                "planner" : "setchaining",
                # // "when_args" : {"cross_rhs_inference" : "implicit_negatives"},
                "function_set" : [
                    # ReverseSign,
                    # EvalArithmetic,
                    
                    GetOperand,
                    AddTerm,
                    SubTerm,
                    DivTerm,
                    MulTerm,
                    Numerator, 
                    Denominator,
                    ExprVar,
                    ExprConst,
                    ExprCoeff,
                    ExprDenCoeff,
                    WriteMultiply,
                    WriteDivide,
                    WriteSubtract,
                    WriteAdd],
                "feature_set" : [
                    GetOperator,
                    ExprVar,
                    ExprConst,
                    ExprCoeff,
                    ExprDenCoeff,
                ],
                # "feature_set" : ['Equals'],
                "extra_features" : [],
                "find_neighbors" : True,
                # "strip_attrs" : ["to_left","to_right","above","below","type","id","offsetParent","dom_class"],
                # "state_variablization" : "metaskill",
                "when_args": {"encode_relative" : True, "one_hot": False },
            }
            agent = CREAgent(**agent_args)
        elif(args.agent_type.upper() == "RHS_LHS"):
            from apprentice.agents.RHS_LHS_Agent import RHS_LHS_Agent
            agent = RHS_LHS_Agent(**agent_args)
        else:
            raise ValueError(f"Unrecognized agent type {args.agent_type!r}.")

        run_training(agent, logger_name=logger_name,  n=int(args.n_problems), n_rows=args.n_rows)
