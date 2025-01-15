''' TODO: Need to suss out what is necessary here... much of this should surely be deprecated
    Also not sure how I feel about this being in an __init__.py file which causes an implicit execution.
    We should be trying to isolate dependencies where possible---i.e. installing tutorgym shouldn't 
    involve installing every dependency for every agent that might use tutorgym.


from gym.envs.registration import register
from tutorgym.fractions import FractionArithNumberEnv  # noqa: F401
from tutorgym.fractions import FractionArithDigitsEnv  # noqa: F401
from tutorgym.fractions import FractionArithOppEnv  # noqa: F401
from tutorgym.multicolumn import MultiColumnAdditionDigitsEnv  # noqa: F401
from tutorgym.multicolumn import MultiColumnAdditionPixelEnv  # noqa: F401
from tutorgym.multicolumn import MultiColumnAdditionPerceptEnv  # noqa: F401
from tutorgym.multicolumn import MultiColumnAdditionOppEnv  # noqa: F401
from tutorgym.multicolumn_std import MultiColumnAdditionDigitsGymEnv  # noqa: F401

register(
    id='FractionArith-v0',
    entry_point='tutorenvs:FractionArithNumberEnv',
)

register(
    id='FractionArith-v1',
    entry_point='tutorenvs:FractionArithOppEnv',
)

register(
    id='FractionArith-v2',
    entry_point='tutorenvs:FractionArithDigitsEnv',
)

# TODO no pixel fractions yet.
# register(
#     id='FractionArith-v2',
#     entry_point='tutorenvs:FractionArithPixelEnv',
# )

# These are Chris's
register(
    id='MulticolumnArithSymbolic-v0',
    entry_point='tutorenvs:MultiColumnAdditionDigitsEnv',
)

register(
    id='MulticolumnArithSymbolic-v1',
    entry_point='tutorenvs:MultiColumnAdditionOppEnv',
)

register(
    id='MulticolumnArithPixel-v0',
    entry_point='tutorenvs:MultiColumnAdditionPixelEnv',
)

register(
    id='MulticolumnArithPercept-v0',
    entry_point='tutorenvs:MultiColumnAdditionPerceptEnv',
)

# This one is Danny's
register(
    id='MulticolumnAdditionSTD_SZ-v0',
    entry_point='tutorenvs:MultiColumnAdditionDigitsGymEnv',
    kwargs={'n_digits' : 3, 'carry_zero' : False},
)

register(
    id='MulticolumnAdditionSTD_CZ-v0',
    entry_point='tutorenvs:MultiColumnAdditionDigitsGymEnv',
    kwargs={'n_digits' : 3, 'carry_zero' : True},
)

'''
