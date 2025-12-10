from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Set, Tuple

from tutorgym.shared import Action, ProblemState
from tutorgym.env_classes.CTAT.action_model import CTAT_ActionModel
from tutorgym.env_classes.fsm_tutor import FiniteStateMachine, StateMachineTutor


@dataclass
class Token:

    value: str
    sources: Set[str]

    def clone(self, *, sources: Iterable[str] | None = None, include_existing: bool = False) -> "Token":
        new_sources: Set[str] = set()
        if include_existing:
            new_sources.update(self.sources)
        if sources is not None:
            new_sources.update(sources)
        elif not include_existing:
            new_sources.update(self.sources)
        return Token(self.value, new_sources)


class SubstitutionTutorV2(StateMachineTutor):

    def __init__(self, problems: Sequence[Dict] | None = None, **kwargs):
        super().__init__(action_model=CTAT_ActionModel, **kwargs)
        self._problem_bank = list(problems or self._default_problem_bank())
        self._random_generators = [
            self._random_inventory_problem,
            self._random_production_problem,
            self._random_ratio_problem,
        ]
        self.substitution_targets: List[Tuple[str, str, List[str]]] = []
        self.possible_selections: List[str] = []
        self.possible_args: List[str] = []
        self.set_random_problem()

    # ------------------------------------------------------------------
    # Problem creation helpers
    # ------------------------------------------------------------------
    def _default_problem_bank(self) -> Sequence[Dict]:
        return [
            {
                "variables": ["M", "P", "G", "B", "W"],
                "quantities": {"W": "150", "P": "18"},
                "relationships": [
                    "G = 2 * P",
                    "B = 2/5 * W",
                    "M + P + G + B = W",
                ],
                "unknowns": ["M"],
            },
            {
                "variables": ["S", "D", "T"],
                "quantities": {"D": "42"},
                "relationships": [
                    "T = 3 * D",
                    "S + T = 5 * D",
                ],
                "unknowns": ["S"],
            },
            {
                "variables": ["X", "Y", "Z"],
                "quantities": {"X": "4/7", "Y": "28"},
                "relationships": [
                    "X * Z = Y",
                ],
                "unknowns": ["Z"],
            },
            {
                "variables": ["W", "E", "T"],
                "quantities": {"E": "12", "T": "50/60"},
                "relationships": [
                    "W = E * T",
                ],
                "unknowns": ["W"],
            },
        ]

    def set_random_problem(self):
        if self._random_generators and random.random() < 0.5:
            problem = self.generate_random_problem()
        else:
            problem = random.choice(self._problem_bank)
        self.set_problem(**problem)
        return problem

    def generate_random_problem(self) -> Dict:
        generator = random.choice(self._random_generators)
        return generator()

    def set_start_state(
        self,
        variables: Sequence[str],
        quantities: Dict[str, str],
        relationships: Sequence[str],
        unknowns: Sequence[str],
    ) -> None:
        if not unknowns:
            raise ValueError("Problem must supply at least one unknown.")
        self.variables = list(variables)
        self.quantities = dict(quantities)
        self.relationships = list(relationships)
        self.unknown = unknowns[0]

        (
            start_state,
            substitution_targets,
            locked_ids,
            substitution_ids,
        ) = self._build_state()

        self.start_state = start_state
        self.substitution_targets = substitution_targets
        self.possible_args = sorted(locked_ids)
        self.possible_selections = substitution_ids + ["done"]

        self.problem = {
            "variables": self.variables,
            "quantities": self.quantities,
            "relationships": self.relationships,
            "unknown": self.unknown,
        }
        self.problem_name = f"substitution_v2_{self.unknown}"
        self.problem_type = "SUBSTITUTION_V2"

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

    def _tokenize(self, text: str) -> List[str]:
        for symbol in ["=", "+", "-", "*", "(", ")"]:
            text = text.replace(symbol, f" {symbol} ")
        return [tok for tok in text.split() if tok]

    def _tokenize_quantity_value(self, value: str) -> List[str]:
        tokens: List[str] = []
        current = []
        for char in value:
            if char == "/":
                if current:
                    tokens.append("".join(current).strip())
                    current = []
                tokens.append(char)
            else:
                current.append(char)
        if current:
            tokens.append("".join(current).strip())
        tokens = [tok for tok in tokens if tok]
        return tokens or [value]

    def _split_equation(self, tokens: Sequence[str]) -> Tuple[List[str], List[str]]:
        if "=" not in tokens:
            raise ValueError("Relationship must contain '=' sign")
        eq_idx = tokens.index("=")
        return list(tokens[:eq_idx]), list(tokens[eq_idx + 1 :])

    def _build_state(
        self,
    ) -> Tuple[
        ProblemState,
        List[Tuple[str, str, List[str]]],
        List[str],
        List[str],
    ]:
        locked_ids: List[str] = []
        substitution_targets: List[Tuple[str, str, List[str]]] = []
        substitution_ids: List[str] = []

        state: Dict[str, Dict] = {}
        y_offset = 0
        x_step = 130

        def add_row(base_id: str, tokens: Sequence[str], locked: bool, y: int) -> List[str]:
            ids = []
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
                    substitution_ids.append(widget_id)
                ids.append(widget_id)
            return ids

        # Known quantities -----------------------------------------------------------------
        self.known_tokens: Dict[str, List[Token]] = {}
        for q_index, (var, value) in enumerate(sorted(self.quantities.items())):
            value_tokens = self._tokenize_quantity_value(value)
            tokens = [var, "="] + value_tokens
            ids = add_row(f"known{q_index}", tokens, True, y_offset)
            y_offset += 70
            value_widget_ids = ids[2:]
            self.known_tokens[var] = [
                Token(tok, {value_widget_ids[idx]})
                for idx, tok in enumerate(value_tokens)
            ]

        # Relationships ---------------------------------------------------------------------
        self.relationship_rhs_tokens: Dict[str, List[Token]] = {}
        relationship_rows: List[Tuple[str, List[str], List[str]]] = []
        for r_index, relationship in enumerate(self.relationships):
            tokens = self._tokenize(relationship)
            ids = add_row(f"relationship{r_index}", tokens, True, y_offset)
            y_offset += 70
            relationship_rows.append((relationship, tokens, ids))

        for relationship, tokens, ids in relationship_rows:
            lhs_tokens, rhs_tokens = self._split_equation(tokens)
            eq_index = tokens.index("=")

            rhs_token_objs = [
                Token(tokens[idx], {ids[idx]})
                for idx in range(eq_index + 1, len(tokens))
            ]
            lhs_token_objs = [
                Token(tokens[idx], {ids[idx]})
                for idx in range(eq_index)
            ]

            if len(lhs_tokens) == 1:
                lhs_var = lhs_tokens[0]
                if lhs_var in self.variables:
                    self.relationship_rhs_tokens[lhs_var] = rhs_token_objs
                    continue

            if len(rhs_tokens) == 1:
                rhs_var = rhs_tokens[0]
                if rhs_var in self.variables:
                    self.relationship_rhs_tokens[rhs_var] = lhs_token_objs

        # Build substitution targets --------------------------------------------------------
        target_relationship = None
        target_tokens_ids = None
        rhs_fallback = None
        rhs_fallback_ids = None
        for relationship, tokens, ids in relationship_rows:
            lhs_tokens, rhs_tokens = self._split_equation(tokens)
            if self.unknown in lhs_tokens:
                target_relationship = tokens
                target_tokens_ids = ids
                break
            if rhs_fallback is None and self.unknown in rhs_tokens:
                rhs_fallback = tokens
                rhs_fallback_ids = ids

        if not target_relationship and rhs_fallback:
            target_relationship = rhs_fallback
            target_tokens_ids = rhs_fallback_ids

        if not target_relationship or not target_tokens_ids:
            raise ValueError(f"No relationship includes unknown '{self.unknown}'.")

        target_tokens = [Token(tok, {target_tokens_ids[idx]}) for idx, tok in enumerate(target_relationship)]
        substituted_tokens = self._expand_tokens(target_tokens)

        substitution_row_ids = add_row("substitution", [t.value for t in substituted_tokens], False, y_offset)
        for widget_id, token in zip(substitution_row_ids, substituted_tokens):
            substitution_targets.append((widget_id, token.value, sorted(token.sources)))

        # Done button ----------------------------------------------------------------------
        state["done"] = {
            "x": 0,
            "y": y_offset + 80,
            "type": "Button",
            "width": 160,
            "height": 60,
            "id": "done",
        }

        return ProblemState(state), substitution_targets, locked_ids, substitution_ids

    # ------------------------------------------------------------------
    # Token expansion
    # ------------------------------------------------------------------
    def _expand_tokens(self, tokens: List[Token]) -> List[Token]:
        result: List[Token] = []
        for token in tokens:
            replacement = self._maybe_replace(token)
            result.extend(replacement)
        changed = True
        while changed:
            changed = False
            new_result: List[Token] = []
            for token in result:
                expanded = self._maybe_replace(token)
                if len(expanded) != 1 or expanded[0].value != token.value:
                    changed = True
                new_result.extend(expanded)
            result = new_result
        return result

    def _maybe_replace(self, token: Token) -> List[Token]:
        value = token.value
        if value == self.unknown:
            return [token]

        quantity_tokens = self.known_tokens.get(value)
        if quantity_tokens:
            return [t.clone(include_existing=False) for t in quantity_tokens]

        relationship_tokens = self.relationship_rhs_tokens.get(value)
        if relationship_tokens:
            replacements = [
                t.clone(include_existing=False) for t in relationship_tokens
            ]
            if (
                len(replacements) > 1
                and not (
                    replacements[0].value == "(" and replacements[-1].value == ")"
                )
            ):
                replacements = [Token("(", set())] + replacements + [
                    Token(")", set())
                ]
            return replacements

        return [token]

    # ------------------------------------------------------------------
    # FSM hooks
    # ------------------------------------------------------------------
    def action_is_done(self, action: Action) -> bool:
        return action.selection == "done"

    def create_fsm(self, state: ProblemState, **_) -> FiniteStateMachine:
        curr_state = state
        fsm = FiniteStateMachine(curr_state, self.action_model)

        for widget_id, token_value, sources in self.substitution_targets:
            action = Action(
                (widget_id, "UpdateTextField", token_value),
                arg_foci=sources,
                how_help="Copy from references",
            )
            curr_state = fsm.add_edge(curr_state, self._validate_action(action))

        done_action = Action(("done", "PressButton", -1), how_help="-1")
        fsm.add_edge(curr_state, self._validate_action(done_action))
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
    # Random problem generation
    # ------------------------------------------------------------------
    def _random_inventory_problem(self) -> Dict:
        total = random.randrange(120, 221, 5)
        price = random.randrange(12, 25)
        g_factor = random.choice([2, 3, 4])
        frac_num = random.choice([1, 2, 3])
        frac_den = random.choice([4, 5, 6])

        return {
            "variables": ["M", "P", "G", "B", "W"],
            "quantities": {"W": str(total), "P": str(price)},
            "relationships": [
                f"G = {g_factor} * P",
                f"B = {frac_num}/{frac_den} * W",
                "M + P + G + B = W",
            ],
            "unknowns": ["M"],
        }

    def _random_production_problem(self) -> Dict:
        demand = random.randrange(24, 55)
        t_factor = random.choice([2, 3, 4])
        total_factor = t_factor + random.choice([1, 2, 3])

        return {
            "variables": ["S", "D", "T"],
            "quantities": {"D": str(demand)},
            "relationships": [
                f"T = {t_factor} * D",
                f"S + T = {total_factor} * D",
            ],
            "unknowns": ["S"],
        }

    def _random_ratio_problem(self) -> Dict:
        numerator = random.randrange(2, 9)
        denominator = random.randrange(3, 9)
        multiplier = random.randrange(2, 10)
        fraction = f"{numerator}/{denominator}"
        y_value = numerator * multiplier

        return {
            "variables": ["X", "Y", "Z"],
            "quantities": {"X": fraction, "Y": str(y_value)},
            "relationships": [
                "X * Z = Y",
            ],
            "unknowns": ["Z"],
        }