"""Evidence returned by sources, and how it is combined with an LLM premise.

``combine`` is the whole grounding policy. ``plugin/grounding/grounding_core.metta``
implements the same policy in MeTTa for use inside the agent; keep them in step.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .nal import Term, Truth, fmt, revision, tier


class Verdict(str, Enum):
    SUPPORTS = "SUPPORTS"
    REFUTES = "REFUTES"
    UNKNOWN = "UNKNOWN"
    # Only on grounded premises: the source affirmed a different statement
    # (reversed relation, different value) and the agent should use that one.
    CORRECTED = "CORRECTED"


class SourceClass(float, Enum):
    """Initial confidence per source class, from Omega's tutorial-07."""

    PRIMARY = 0.9
    VERIFIED_SECONDARY = 0.7
    GENERAL_SECONDARY = 0.55
    TERTIARY = 0.4


# Omega's failure-mode report: LLM-assigned confidence runs ~15 points high.
DEFAULT_LLM_DISCOUNT = 0.15
NO_EVIDENCE = Truth(0.5, 0.0)


def _clean(text: str) -> str:
    return " ".join(text.replace('"', "'").replace("\\", "/").split())


@dataclass(frozen=True)
class Evidence:
    verdict: Verdict
    truth: Truth  # evidence about the queried statement
    source: str
    provenance: str
    correction: Optional[Term] = None  # a statement the source affirms instead

    @staticmethod
    def unknown(reason: str, source: str = "none") -> "Evidence":
        return Evidence(Verdict.UNKNOWN, NO_EVIDENCE, source, reason)

    def to_metta(self) -> str:
        correction = fmt(self.correction) if self.correction is not None else "none"
        return (f"(evidence {self.verdict.value} {self.truth} (correction {correction}) "
                f"\"{_clean(self.source + ': ' + self.provenance)}\")")


@dataclass(frozen=True)
class GroundedPremise:
    verdict: Verdict
    statement: Term
    truth: Truth
    tier: str
    evidence: Evidence

    def to_metta(self) -> str:
        prov = _clean(self.evidence.source + ": " + self.evidence.provenance)
        return (f"(grounded {self.verdict.value} ({fmt(self.statement)} {self.truth}) "
                f"{self.tier} \"{prov}\")")


def discount(t: Truth, amount: float) -> Truth:
    return Truth(t.f, max(0.0, t.c - amount))


def combine(statement: Term, llm_truth: Truth, evidence: Evidence,
            llm_discount: float = DEFAULT_LLM_DISCOUNT) -> GroundedPremise:
    """Fold source evidence into an LLM premise.

    - The LLM's confidence is discounted for its measured overconfidence.
    - If the source affirms a different statement and the LLM was asserting
      (f >= 0.5), the premise is replaced by the source's statement.
    - Otherwise the evidence is merged with NAL revision. Evidence with zero
      confidence (UNKNOWN) leaves the discounted prior unchanged.
    """
    prior = discount(llm_truth, llm_discount)
    if evidence.correction is not None and llm_truth.f >= 0.5:
        truth = Truth(1.0, evidence.truth.c)
        return GroundedPremise(Verdict.CORRECTED, evidence.correction, truth, tier(truth), evidence)
    truth = prior if evidence.truth.c < 0.001 else revision(prior, evidence.truth)
    return GroundedPremise(evidence.verdict, statement, truth, tier(truth), evidence)
