"""Functions the Omega plugin calls through py-call.

They take and return MeTTa source text so the MeTTa side can `sread` the
result, and they never raise: a failure comes back as UNKNOWN evidence, which
leaves the agent's premise unchanged apart from the confidence discount.

Environment:
    OMEGA_GROUNDING_RPC_URL     Ethereum JSON-RPC endpoint
    OMEGA_GROUNDING_MODE        live (default) | record | replay
    OMEGA_GROUNDING_CASSETTE    cassette file for record/replay
"""

from __future__ import annotations

import os
from pathlib import Path

from .evidence import DEFAULT_LLM_DISCOUNT, Evidence
from .grounder import Grounder, default_grounder
from .nal import Truth, parse_premise

_grounder = None


def _get() -> Grounder:
    global _grounder
    if _grounder is None:
        mode = os.environ.get("OMEGA_GROUNDING_MODE", "live")
        cassette = os.environ.get("OMEGA_GROUNDING_CASSETTE")
        _grounder = default_grounder(Path(cassette) if cassette else None, mode)
    return _grounder


def lookup(premise) -> str:
    """Evidence for the statement in `premise`, as an (evidence ...) expression."""
    try:
        statement, _ = parse_premise(str(premise))
        return _get().evidence(statement).to_metta()
    except Exception as exc:
        return Evidence.unknown(f"bridge error: {exc}").to_metta()


def ground(premise, llm_discount=DEFAULT_LLM_DISCOUNT) -> str:
    """The whole pipeline in Python, as a (grounded ...) expression."""
    try:
        statement, truth = parse_premise(str(premise))
        return _get().ground(statement, truth or Truth(1.0, 0.9)).to_metta()
    except Exception as exc:
        return f'(grounding-error "{exc}")'.replace("\n", " ")


def to_float(value) -> float:
    return float(str(value).strip('"'))
