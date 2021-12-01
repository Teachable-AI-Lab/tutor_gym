from tutorenvs.multicolumn_v import MultiColumnAdditionSymbolic
from colorama import Fore, Back


def _assert_step(env, selection, value):
    sai = env.get_demo()
    assert sai[0] == selection
    assert sai[2]['value'] == str(value)

    assert env.apply_sai(selection,  "UpdateTextField", { "value": str(value+1) }) == -1
    assert env.apply_sai(selection,  "UpdateTextField", { "value": str(value) }) == 1


def _assert_done(env):
    sai = env.get_demo()
    assert sai[0] == 'done'
    assert sai[1] == 'ButtonPressed'
    assert sai[2]['value'] == -1

    assert env.apply_sai('done',  "ButtonPressed", { "value": -1 }) == 1


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


if __name__ == "__main__":
    test_multi_column_env()