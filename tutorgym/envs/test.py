from tutorgym.fractions_v import FractionArithSymbolic
from tutorgym.multicolumn_v import MultiColumnAdditionSymbolic
from colorama import Fore, Back
from tutorgym.utils import compare


def _assert_step(env, selection, value, fraction=False):
    sai = env.get_demo()
    assert sai[0] == selection
    assert sai[2]['value'] == str(value)


    action = "UpdateField" if fraction else "UpdateTextField"
    assert env.apply_sai(selection, action, { "value": str(value+1) }) == -1
    assert env.apply_sai(selection, action, { "value": str(value) }) == 1

def _assert_check_convert(env):
    sai = env.get_demo()
    assert sai[0] == 'check_convert'
    assert sai[1] == 'UpdateField'
    assert sai[2]['value'] == 'x'

    assert env.apply_sai('check_convert',  "UpdateField", { "value": 'x' }) == 1

def _assert_done(env):
    sai = env.get_demo()
    assert sai[0] == 'done'
    assert sai[1] == 'ButtonPressed'
    assert sai[2]['value'] == -1

    assert env.apply_sai('done',  "ButtonPressed", { "value": -1 }) == 1


def test_fraction_env():
    # AD
    env = FractionArithSymbolic(n=3)
    env.set_problem([1, 2, 3], [2, 3, 4], '+')
    print(Fore.RESET + Back.RESET)

    _assert_check_convert(env)

    steps = [
        ("convert_denom_0", 24),
        ("convert_denom_1", 24),
        ("convert_denom_2", 24),
        ("convert_num_0", 12),
        ("convert_num_1", 16),
        ("convert_num_2", 18),
        ("answer_num", 46),
        ("answer_denom", 24),
    ]

    for s in steps:
        _assert_step(env, s[0], s[1], fraction=True)

    _assert_done(env)

    # AS
    env = FractionArithSymbolic(n=4)
    env.set_problem([1, 1, 2, 2], [8, 8, 8, 8], '+')
    print(Fore.RESET + Back.RESET)

    steps = [
        ("answer_num", 6),
        ("answer_denom", 8),
    ]
    for s in steps:
        _assert_step(env, s[0], s[1], fraction=True)
    _assert_done(env)

    # M
    env = FractionArithSymbolic(n=3)
    env.set_problem([1, 2, 3], [2, 3, 4], '*')
    print(Fore.RESET + Back.RESET)

    steps = [
        ("answer_num", 6),
        ("answer_denom", 24),
    ]
    for s in steps:
        _assert_step(env, s[0], s[1], fraction=True)
    _assert_done(env)

    print("PASS")


def test_multi_column_env():
    env = MultiColumnAdditionSymbolic(n=3)
    env.set_problem(654, 553)
    print(Fore.RESET + Back.RESET)

    steps = [
        ("0_answer", 7),
        ("1_answer", 0),
        ("2_carry", 1),
        ("2_answer", 2),
        ("3_carry", 1),
        ("3_answer", 1),
    ]

    for s in steps:
        print(s)
        _assert_step(env, s[0], s[1])

    _assert_done(env)

    env = MultiColumnAdditionSymbolic(n=2)
    env.set_problem(99, 99)
    print(Fore.RESET + Back.RESET)

    steps = [
        ("0_answer", 8),
        ("1_carry", 1),
        ("1_answer", 9),
        ("2_carry", 1),
        ("2_answer", 1),
    ]

    for s in steps:
        print(s)
        _assert_step(env, s[0], s[1])

    _assert_done(env)
    print("PASS")


def test_compare():
    assert compare([1, 2, 3], [1, 2, 3])
    assert not compare([1, 2, 3], [1, 3, 3])

    x = {"x": {"a": 1, "b": 2}, "y": "hello" }
    y = {"x": {"a": 1, "b": 2}, "y": "hello" }

    assert compare(x, y)
    y["y"] = "world"
    assert not compare(x, y)


if __name__ == "__main__":
    # test_multi_column_env()
    # test_fraction_env()
    test_compare()
