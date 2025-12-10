from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Sequence, Set, Tuple

from sympy import Eq, simplify, sstr, symbols
from sympy.parsing.sympy_parser import parse_expr
from sympy.solvers import solve

from tutorgym.env_classes.CTAT.action_model import CTAT_ActionModel
from tutorgym.env_classes.fsm_tutor import FiniteStateMachine, StateMachineTutor
from tutorgym.shared import Action, ProblemState


@dataclass
class Token:

    value: str
    sources: Set[str]

    def clone(
        self,
        *,
        sources: Iterable[str] | None = None,
        include_existing: bool = False,
    ) -> "Token":
        new_sources: Set[str] = set()
        if include_existing:
            new_sources.update(self.sources)
        if sources is not None:
            new_sources.update(sources)
        elif not include_existing:
            new_sources.update(self.sources)
        return Token(self.value, new_sources)


class CalculationTutor(StateMachineTutor):

    def __init__(self, problems: Sequence[Dict] | None = None, **kwargs):
        super().__init__(action_model=CTAT_ActionModel, **kwargs)
        self._problem_bank = list(problems or self._default_problem_bank())
        self.solution_targets: List[Tuple[str, str, List[str]]] = []
        self.possible_selections: List[str] = []
        self.possible_args: List[str] = []
        self.set_random_problem()

    # ------------------------------------------------------------------
    # Problem helpers
    # ------------------------------------------------------------------
    def _default_problem_bank(self) -> Sequence[Dict]:
        return [
            {
                "equation_tokens": [
                    "a",
                    "+",
                    "(",
                    "2",
                    "*",
                    "a",
                    ")",
                    "+",
                    "(",
                    "2",
                    "*",
                    "(",
                    "2",
                    "*",
                    "a",
                    ")",
                    ")",
                    "=",
                    "847",
                ],
                "unknown": "a",
            },
            {
                "equation_tokens": [
                    "t",
                    "=",
                    "(",
                    "(",
                    "2.5",
                    "*",
                    "6",
                    ")",
                    "*",
                    "(",
                    "500",
                    "*",
                    "5",
                    "*",
                    "20",
                    ")",
                    ")",
                    "-",
                    "(",
                    "6",
                    "*",
                    "(",
                    "500",
                    "*",
                    "5",
                    "*",
                    "20",
                    ")",
                    ")",
                    "-",
                    "2000",
                ],
                "unknown": "t",
            },
            {
                "equation_tokens": [
                    "M",
                    "+",
                    "18",
                    "+",
                    "2",
                    "*",
                    "18",
                    "+",
                    "2/5",
                    "*",
                    "150",
                    "=",
                    "150",
                ],
                "unknown": "M",
            },
        ]

    def set_random_problem(self):
        problem = self.generate_random_problem()
        self.set_problem(**problem)
        return problem

    def generate_random_problem(self) -> Dict:
        if random.random() < 0.5:
            return random.choice(self._problem_bank)
        return self._random_linear_problem()

    # ------------------------------------------------------------------
    # Environment hooks
    # ------------------------------------------------------------------
    def set_start_state(
        self,
        equation_tokens: Sequence[str],
        unknown: str,
        problem_index: int | None = None,
        variant_index: int | None = None,
    ) -> None:
        if not equation_tokens:
            raise ValueError("Equation must contain at least one token.")
        if unknown not in equation_tokens:
            raise ValueError("Unknown variable must appear in the equation tokens.")

        self.equation_tokens = list(equation_tokens)
        self.unknown = unknown

        (
            start_state,
            solution_targets,
            locked_ids,
            solution_ids,
        ) = self._build_state()

        self.start_state = start_state
        self.solution_targets = solution_targets
        self.possible_args = sorted(locked_ids)
        self.possible_selections = solution_ids + ["done"]

        self.problem = {
            "equation_tokens": self.equation_tokens,
            "unknown": self.unknown,
        }
        if problem_index is not None:
            self.problem["problem_index"] = problem_index
        if variant_index is not None:
            self.problem["variant_index"] = variant_index

        suffix_parts = [self.unknown]
        if problem_index is not None:
            suffix_parts.append(str(problem_index))
        if variant_index is not None:
            suffix_parts.append(f"v{variant_index}")
        problem_suffix = "_".join(suffix_parts)

        self.problem_name = f"calculation_{problem_suffix}"
        self.problem_type = "CALCULATION"

    # ------------------------------------------------------------------
    # Layout helpers
    # ------------------------------------------------------------------
    def _blank_params(self, locked: bool, value: str = "") -> Dict:
        return {
            "type": "TextField",
            "locked": locked,
            "value": value if locked else "",
            "width": 120,
            "height": 60,
        }

    def _build_state(
        self,
    ) -> Tuple[ProblemState, List[Tuple[str, str, List[str]]], List[str], List[str]]:
        locked_ids: List[str] = []
        solution_targets: List[Tuple[str, str, List[str]]] = []
        solution_ids: List[str] = []

        state: Dict[str, Dict] = {}
        y_offset = 0
        x_step = 130

        def add_row(base_id: str, tokens: Sequence[str], locked: bool, y: int) -> List[str]:
            ids: List[str] = []
            for idx, token in enumerate(tokens):
                widget_id = f"{base_id}_{idx}"
                state[widget_id] = {
                    "x": idx * x_step,
                    "y": y,
                    **self._blank_params(locked, token),
                    "id": widget_id,
                }
                if locked:
                    locked_ids.append(widget_id)
                else:
                    solution_ids.append(widget_id)
                ids.append(widget_id)
            return ids

        equation_ids = add_row("relationship", self.equation_tokens, True, y_offset)
        equation_tokens = [
            Token(tok, {widget_id}) for tok, widget_id in zip(self.equation_tokens, equation_ids)
        ]
        y_offset += 70

        solution_tokens = self._compute_solution_tokens(equation_tokens)

        solution_row_ids = add_row(
            "calculation", [tok.value for tok in solution_tokens], False, y_offset
        )

        operator_values = {"+", "-", "*", "/"}
        for idx, (widget_id, token) in enumerate(zip(solution_row_ids, solution_tokens)):
            sources: List[str] = [] if token.value in operator_values else sorted(token.sources)
            solution_targets.append((widget_id, token.value, sources))

        state["done"] = {
            "x": 0,
            "y": y_offset + 80,
            "type": "Button",
            "width": 160,
            "height": 60,
            "id": "done",
        }

        return ProblemState(state), solution_targets, locked_ids, solution_ids

    # ------------------------------------------------------------------
    # Calculation logic
    # ------------------------------------------------------------------
    def _compute_solution_tokens(self, equation_tokens: List[Token]) -> List[Token]:
        values = [token.value for token in equation_tokens]
        if "=" not in values:
            raise ValueError("Equation tokens must include '='.")
        eq_idx = values.index("=")
        lhs_tokens = values[:eq_idx]
        rhs_tokens = values[eq_idx + 1 :]

        if not any(value == self.unknown for value in lhs_tokens):
            raise ValueError(
                f"Equation must contain the unknown variable '{self.unknown}' on the left-hand side."
            )

        unknown_symbol = symbols(self.unknown)
        lhs_expr = self._parse_expression(lhs_tokens, unknown_symbol)
        rhs_expr = self._parse_expression(rhs_tokens, unknown_symbol)
        equation = Eq(lhs_expr, rhs_expr)
        solutions = solve(equation, unknown_symbol, dict=True)
        if not solutions:
            raise ValueError(f"Unable to solve equation for unknown '{self.unknown}'.")

        solution_expr = simplify(solutions[0][unknown_symbol])
        solution_str = sstr(solution_expr)

        unknown_sources = self._collect_sources(equation_tokens[:eq_idx], self.unknown)
        equals_sources = self._collect_sources([equation_tokens[eq_idx]], "=")
        numeric_operand_sources = self._collect_operand_sources(
            equation_tokens,
            exclude_values={self.unknown, "="},
            predicate=self._is_numeric_value,
        )

        result = [
            Token(self.unknown, unknown_sources),
            Token("=", equals_sources),
            Token(solution_str, numeric_operand_sources),
        ]
        return result

    def _collect_sources(self, tokens: Sequence[Token], target_value: str) -> Set[str]:
        sources: Set[str] = set()
        for token in tokens:
            if token.value == target_value:
                sources.update(token.sources)
        return sources

    def _collect_operand_sources(
        self,
        tokens: Sequence[Token],
        *,
        exclude_values: Set[str],
        predicate: Callable[[str], bool] | None = None,
    ) -> Set[str]:
        sources: Set[str] = set()
        for token in tokens:
            if token.value in exclude_values:
                continue
            if predicate is not None and not predicate(token.value):
                continue
            sources.update(token.sources)
        return sources

    def _is_numeric_value(self, value: str) -> bool:
        try:
            expr = parse_expr(value, evaluate=True)
        except Exception:
            return False
        return not getattr(expr, "free_symbols", set())

    def _parse_expression(self, tokens: Sequence[str], unknown_symbol):
        if not tokens:
            return parse_expr("0", local_dict={self.unknown: unknown_symbol})
        expr_str = " ".join(tokens)
        local_dict = {self.unknown: unknown_symbol}
        return parse_expr(expr_str, local_dict=local_dict, evaluate=True)

    # ------------------------------------------------------------------
    # FSM helpers
    # ------------------------------------------------------------------
    def action_is_done(self, action: Action) -> bool:
        return action.selection == "done"

    def create_fsm(self, state: ProblemState, **_) -> FiniteStateMachine:
        current_state = state
        fsm = FiniteStateMachine(current_state, self.action_model)

        for idx, (widget_id, token_value, sources) in enumerate(self.solution_targets):
            is_final_token = idx == len(self.solution_targets) - 1
            arg_foci = sources
            action = Action(
                (widget_id, "UpdateTextField", token_value),
                arg_foci=arg_foci,
                how_help="Compute value" if is_final_token or not sources else "Copy from references",
            )
            current_state = fsm.add_edge(current_state, self._validate_action(action))

        done_action = Action(("done", "PressButton", -1), how_help="-1")
        fsm.add_edge(current_state, self._validate_action(done_action))
        return fsm

    def get_possible_selections(self) -> List[str]:
        return self.possible_selections

    def get_possible_args(self) -> List[str]:
        return self.possible_args

    def _validate_action(self, action: Action) -> Action:
        selection, action_type, _ = action.as_tuple()
        if selection not in self.possible_selections:
            raise ValueError(f"Unknown selection '{selection}' in demonstration.")
        if action_type not in {"UpdateTextField", "PressButton"}:
            raise ValueError(f"Unsupported action type '{action_type}'.")
        arg_foci = action.annotations.get("arg_foci", []) or []
        invalid = [focus for focus in arg_foci if focus not in self.possible_args]
        if invalid:
            raise ValueError(f"Unknown focus ids {invalid} in demonstration.")
        return action

    # ------------------------------------------------------------------
    # Randomisation
    # ------------------------------------------------------------------
    def _random_linear_problem(self) -> Dict:
        unknown = random.choice(["x", "y", "m", "n"])
        base_value = random.randint(5, 40)
        term_count = random.randint(2, 4)

        lhs_tokens: List[str] = [unknown]
        coefficient_sum = 1

        for _ in range(term_count - 1):
            coef = random.randint(2, 6)
            coefficient_sum += coef
            term_tokens = self._build_term_tokens(coef, unknown)
            lhs_tokens.append("+")
            lhs_tokens.extend(term_tokens)

        rhs_value = coefficient_sum * base_value
        equation_tokens = lhs_tokens + ["=", str(rhs_value)]

        return {"equation_tokens": equation_tokens, "unknown": unknown}

    def _build_term_tokens(self, coefficient: int, unknown: str) -> List[str]:
        tokens = [str(coefficient), "*", unknown]
        if random.random() < 0.5:
            tokens = ["("] + tokens + [")"]
        if random.random() < 0.3:
            inner_coef = random.randint(2, 4)
            tokens = ["(", str(inner_coef), "*", "("] + tokens + [")", ")"]
        return tokens