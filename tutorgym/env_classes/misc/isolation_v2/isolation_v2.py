from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Set, Tuple

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


@dataclass
class Term:

    operator: Token | None
    tokens: List[Token]

    def contains_unknown(self, unknown: str) -> bool:
        return any(token.value == unknown for token in self.tokens)

    def sign(self) -> int:
        if self.operator and self.operator.value == "-":
            return -1
        return 1


class IsolationTutorV2(StateMachineTutor):

    def __init__(self, problems: Sequence[Dict] | None = None, **kwargs):
        super().__init__(action_model=CTAT_ActionModel, **kwargs)
        self._problem_bank = list(problems or self._default_problem_bank())
        self.isolation_targets: List[Tuple[str, str, List[str]]] = []
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
            {
                "equation_tokens": [
                    "S",
                    "+",
                    "3",
                    "*",
                    "42",
                    "=",
                    "5",
                    "*",
                    "42",
                ],
                "unknown": "S",
            },
            {
                "equation_tokens": [
                    "V",
                    "+",
                    "12",
                    "+",
                    "4",
                    "*",
                    "15",
                    "=",
                    "120",
                ],
                "unknown": "V",
            },
        ]

    def set_random_problem(self):
        problem = self.generate_random_problem()
        self.set_problem(**problem)
        return problem

    def generate_random_problem(self) -> Dict:
        if random.random() < 0.5:
            return random.choice(self._problem_bank)
        return self._random_additive_problem()

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
            isolation_targets,
            locked_ids,
            isolation_ids,
        ) = self._build_state()

        self.start_state = start_state
        self.isolation_targets = isolation_targets
        self.possible_args = sorted(locked_ids)
        self.possible_selections = isolation_ids + ["done"]

        self.problem = {
            "equation_tokens": self.equation_tokens,
            "unknown": self.unknown,
        }
        if problem_index is not None:
            self.problem["problem_index"] = problem_index
        if variant_index is not None:
            self.problem["variant_index"] = variant_index

        suffix_parts: List[str] = [self.unknown]
        if problem_index is not None:
            suffix_parts.append(str(problem_index))
        if variant_index is not None:
            suffix_parts.append(f"v{variant_index}")

        suffix = "_".join(suffix_parts)
        self.problem_name = f"isolation_{suffix}"
        self.problem_type = "ISOLATION"

    # ------------------------------------------------------------------
    # Layout helpers
    # ------------------------------------------------------------------
    def _blank_params(self, locked: bool, value: str = "") -> Dict:
        return {
            "type": "TextField",
            "locked": locked,
            "value": value,
            "width": 120,
            "height": 60,
        }

    def _build_state(
        self,
    ) -> Tuple[ProblemState, List[Tuple[str, str, List[str]]], List[str], List[str]]:
        locked_ids: List[str] = []
        isolation_targets: List[Tuple[str, str, List[str]]] = []
        isolation_ids: List[str] = []

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
                    **self._blank_params(locked, token if locked else ""),
                    "id": widget_id,
                }
                if locked:
                    locked_ids.append(widget_id)
                else:
                    isolation_ids.append(widget_id)
                ids.append(widget_id)
            return ids

        # Locked relationship row -----------------------------------------------------------
        equation_ids = add_row("relationship", self.equation_tokens, True, y_offset)
        equation_tokens = [
            Token(tok, {widget_id})
            for tok, widget_id in zip(self.equation_tokens, equation_ids)
        ]
        y_offset += 70

        # Isolation row ---------------------------------------------------------------------
        isolation_tokens = self._compute_isolation_tokens(equation_tokens)
        isolation_row_ids = add_row(
            "isolation", [tok.value for tok in isolation_tokens], False, y_offset
        )

        operator_values = {"+", "-", "*", "/"}
        for widget_id, token in zip(isolation_row_ids, isolation_tokens):
            sources = [] if token.value in operator_values else sorted(token.sources)
            isolation_targets.append((widget_id, token.value, sources))

        # Done button -----------------------------------------------------------------------
        state["done"] = {
            "x": 0,
            "y": y_offset + 80,
            "type": "Button",
            "width": 160,
            "height": 60,
            "id": "done",
        }

        return ProblemState(state), isolation_targets, locked_ids, isolation_ids

    # ------------------------------------------------------------------
    # Isolation logic
    # ------------------------------------------------------------------
    def _compute_isolation_tokens(
        self,
        equation_tokens: List[Token],
    ) -> List[Token]:
        values = [token.value for token in equation_tokens]
        if "=" not in values:
            raise ValueError("Equation tokens must include '='.")
        eq_idx = values.index("=")
        lhs_tokens = equation_tokens[:eq_idx]
        rhs_tokens = equation_tokens[eq_idx + 1 :]

        if not any(token.value == self.unknown for token in equation_tokens):
            raise ValueError(
                f"Equation must contain the unknown variable '{self.unknown}'."
            )

        lhs_terms = self._split_terms(lhs_tokens)
        rhs_terms = self._split_terms(rhs_tokens)

        left_specs: List[Tuple[Term, int]] = []
        right_specs: List[Tuple[Term, int]] = []
        left_constants: List[Tuple[Term, int]] = []

        for term in lhs_terms:
            if term.contains_unknown(self.unknown):
                left_specs.append((term, term.sign()))
            else:
                left_constants.append((term, -term.sign()))

        moved_unknown_terms: List[Tuple[Term, int]] = []
        for term in rhs_terms:
            if term.contains_unknown(self.unknown):
                moved_unknown_terms.append((term, -term.sign()))
            else:
                right_specs.append((term, term.sign()))

        left_specs.extend(moved_unknown_terms)
        right_specs.extend(left_constants)

        if not left_specs:
            raise ValueError(
                f"Unable to isolate unknown '{self.unknown}' because no terms contain it."
            )

        rhs_tokens_result = self._assemble_terms(right_specs)
        if not rhs_tokens_result:
            rhs_tokens_result = [Token("0", set())]

        result = self._assemble_terms(left_specs)
        result.append(equation_tokens[eq_idx].clone())
        result.extend(rhs_tokens_result)
        return result

    def _split_terms(self, tokens: List[Token]) -> List[Term]:
        terms: List[Term] = []
        current: List[Token] = []
        pending_operator: Token | None = None
        depth = 0

        for token in tokens:
            value = token.value
            if depth == 0 and value in {"+", "-"}:
                if current:
                    terms.append(Term(pending_operator, current))
                    current = []
                pending_operator = token
                continue

            if value == "(":
                depth += 1
            elif value == ")" and depth > 0:
                depth -= 1

            current.append(token)

        if current:
            terms.append(Term(pending_operator, current))

        return terms

    def _assemble_terms(self, specs: Sequence[Tuple[Term, int]]) -> List[Token]:
        result: List[Token] = []
        first_term = True

        for term, sign in specs:
            if not term.tokens:
                continue

            operator_token: Token | None = None
            if first_term:
                if sign == -1:
                    operator_token = self._create_operator_token(term.operator, "-")
                first_term = False
            else:
                op_value = "+" if sign >= 0 else "-"
                operator_token = self._create_operator_token(term.operator, op_value)

            if operator_token is not None:
                result.append(operator_token)

            result.extend(token.clone() for token in term.tokens)

        return result

    def _create_operator_token(
        self, source: Token | None, value: str
    ) -> Token | None:
        if value not in {"+", "-"}:
            return None

        sources: Set[str] = set()
        if source is not None:
            sources.update(source.sources)
        return Token(value, sources)

    # ------------------------------------------------------------------
    # FSM helpers
    # ------------------------------------------------------------------
    def action_is_done(self, action: Action) -> bool:
        return action.selection == "done"

    def create_fsm(self, state: ProblemState, **_) -> FiniteStateMachine:
        current_state = state
        fsm = FiniteStateMachine(current_state, self.action_model)

        for widget_id, token_value, sources in self.isolation_targets:
            action = Action(
                (widget_id, "UpdateTextField", token_value),
                arg_foci=sources,
                how_help="Copy from references",
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
    def _random_additive_problem(self) -> Dict:
        unknown = random.choice(["M", "S", "A", "N", "X"])
        rhs_value = random.randrange(100, 241, 5)

        single_term = random.randrange(10, 31)

        product_factor = random.randrange(2, 5)
        product_value = random.randrange(10, 40, 2)
        if random.random() < 0.5:
            product_tokens = [str(product_factor), "*", str(product_value)]
        else:
            numerator = product_factor * product_value
            product_tokens = [str(numerator), "/", str(product_factor)]

        frac_num = random.randrange(1, 4)
        frac_den = random.randrange(4, 7)
        if random.random() < 0.5:
            frac_tokens = [f"{frac_num}/{frac_den}", "*", str(rhs_value)]
        else:
            numerator = rhs_value * frac_num
            frac_tokens = [str(numerator), "/", str(frac_den)]

        term_specs: List[Tuple[str, List[str]]] = [
            (random.choice(["+", "-"]), [str(single_term)]),
            (random.choice(["+", "-"]), product_tokens),
            (random.choice(["+", "-"]), frac_tokens),
        ]

        tokens: List[str] = [unknown]
        for sign, term_tokens in term_specs:
            tokens.append(sign)
            tokens.extend(term_tokens)
        tokens.extend(["=", str(rhs_value)])

        return {"equation_tokens": tokens, "unknown": unknown}