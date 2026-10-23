"""Guard for the `nal` skill in tools/agent_run (no Omega dependency, unit-tested)."""

import re

# Heads allowed inside a `nal` expression: inference entry points, copulas, truth values
# and term constructors. Anything else in head position (py-call, import!, eval, ...)
# could run code when the expression is evaluated, so it is rejected.
ALLOWED_HEADS = {
    "|-", "|~", "-->", "<->", "==>", "<=>", "stv", "×", "[]", "{}", "IntSet", "ExtSet",
    "Implication", "Inheritance", "Similarity", "Evaluation", "And", "Or", "Not",
    "&&", "||", "--", "&", "|", "-", "~",
}
ATOM = re.compile(r'^(-?\d+(\.\d+)?|\$?[A-Za-z0-9_.\-]+|"[^"]*")$')


def allowed_inference(text) -> bool:
    """True if text is one (|- ...) or (|~ ...) expression built only from allowed parts."""
    tokens = re.findall(r'\(|\)|"[^"]*"|[^\s()"]+', str(text))
    depth, expect_head, first_head = 0, False, None
    for token in tokens:
        if token == "(":
            depth += 1
            expect_head = True
        elif token == ")":
            depth -= 1
            if depth < 0:
                return False
            expect_head = False
        else:
            if expect_head:
                if token not in ALLOWED_HEADS:
                    return False
                first_head = first_head or token
            elif token not in ALLOWED_HEADS and not ATOM.match(token):
                return False
            expect_head = False
    return depth == 0 and first_head in ("|-", "|~") and tokens[0] == "("
