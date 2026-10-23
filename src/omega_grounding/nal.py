"""MeTTa s-expressions and the NAL truth functions Omega uses.

The truth functions mirror Omega's ``lib_nal.metta`` exactly, including the
clamps in ``Truth_Revision``, so numbers computed here for the benchmark match
what the agent computes inside its reasoning loop.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple, Union

Term = Union[str, Tuple["Term", ...]]

INHERITANCE = "-->"
SIMILARITY = "<->"
IMPLICATION = "==>"
PRODUCT = "×"
INT_SETS = ("[]", "IntSet")


class ParseError(ValueError):
    pass


def _tokenize(text: str):
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if ch.isspace():
            i += 1
        elif ch in "()":
            yield ch
            i += 1
        elif ch == '"':
            j = i + 1
            while j < n and text[j] != '"':
                j += 2 if text[j] == "\\" else 1
            if j >= n:
                raise ParseError(f"unterminated string in {text!r}")
            yield text[i:j + 1]
            i = j + 1
        else:
            j = i
            while j < n and not text[j].isspace() and text[j] not in '()"':
                j += 1
            yield text[i:j]
            i = j


def parse(text: str) -> Term:
    """Parse one s-expression into nested tuples of atom strings."""
    stack: list = [[]]
    for token in _tokenize(text):
        if token == "(":
            stack.append([])
        elif token == ")":
            if len(stack) == 1:
                raise ParseError(f"unbalanced ')' in {text!r}")
            done = tuple(stack.pop())
            stack[-1].append(done)
        else:
            stack[-1].append(token)
    if len(stack) != 1:
        raise ParseError(f"unbalanced '(' in {text!r}")
    if len(stack[0]) != 1:
        raise ParseError(f"expected one expression, got {len(stack[0])} in {text!r}")
    return stack[0][0]


def fmt(term: Term) -> str:
    if isinstance(term, tuple):
        return "(" + " ".join(fmt(t) for t in term) + ")"
    return term


def fmt_number(x: float) -> str:
    """Render a float the way MeTTa sources write them: always with a dot."""
    text = f"{x:.4f}".rstrip("0")
    return text + "0" if text.endswith(".") else text


@dataclass(frozen=True)
class Truth:
    f: float
    c: float

    def to_term(self) -> Term:
        return ("stv", fmt_number(self.f), fmt_number(self.c))

    def __str__(self) -> str:
        return fmt(self.to_term())

    @staticmethod
    def from_term(term: Term) -> "Truth":
        if not (isinstance(term, tuple) and len(term) == 3 and term[0] == "stv"):
            raise ParseError(f"not an (stv f c) truth value: {fmt(term)}")
        return Truth(float(term[1]), float(term[2]))


def parse_premise(text: str) -> Tuple[Term, Optional[Truth]]:
    """Accept ``((--> a b) (stv f c))`` or a bare statement ``(--> a b)``."""
    term = parse(text)
    if (isinstance(term, tuple) and len(term) == 2 and isinstance(term[1], tuple)
            and term[1] and term[1][0] == "stv"):
        return term[0], Truth.from_term(term[1])
    return term, None


def is_statement(term: Term, copula: Optional[str] = None) -> bool:
    return (isinstance(term, tuple) and len(term) == 3
            and term[0] in (INHERITANCE, SIMILARITY, IMPLICATION)
            and (copula is None or term[0] == copula))


def normalize(term: Term) -> Term:
    """Case-fold atoms so 'Dolphin' and 'dolphin' compare equal (strings kept)."""
    if isinstance(term, tuple):
        return tuple(normalize(t) for t in term)
    return term if term.startswith('"') else term.lower()


def reverse(statement: Term) -> Term:
    """Swap subject and predicate - the relation-swap error Omega measures."""
    copula, subject, predicate = statement
    return (copula, predicate, subject)


# --- Truth functions (mirror lib_nal.metta) ---------------------------------

def c2w(c: float) -> float:
    return c / (1 - c)


def w2c(w: float) -> float:
    return w / (w + 1)


def deduction(t1: Truth, t2: Truth) -> Truth:
    f = t1.f * t2.f
    return Truth(f, f * t1.c * t2.c)


def revision(t1: Truth, t2: Truth) -> Truth:
    """Omega's Truth_Revision, clamps included."""
    w1, w2 = c2w(t1.c), c2w(t2.c)
    w = w1 + w2
    f = (w1 * t1.f + w2 * t2.f) / w
    c = w2c(w)
    return Truth(min(1.0, f), min(0.99, max(c, t1.c, t2.c)))


def expectation(t: Truth) -> float:
    return t.c * (t.f - 0.5) + 0.5


# Action tiers from Omega's docs/reference-orchestration.md.
ACT = "ACT"
HYPOTHESIZE = "HYPOTHESIZE"
IGNORE = "IGNORE"


def tier(t: Truth) -> str:
    if t.f >= 0.6 and t.c >= 0.5:
        return ACT
    if t.f >= 0.3 and t.c >= 0.2:
        return HYPOTHESIZE
    return IGNORE
