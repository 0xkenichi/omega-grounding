import pytest

from omega_grounding.evidence import Evidence, Verdict, combine
from omega_grounding.nal import ACT, HYPOTHESIZE, Truth

STATEMENT = ("-->", "mammal", "dolphin")
CORRECT = ("-->", "dolphin", "mammal")


def swap_evidence():
    return Evidence(Verdict.REFUTES, Truth(0.0, 0.7), "wikidata", "reverse", correction=CORRECT)


def test_unknown_evidence_only_discounts():
    g = combine(STATEMENT, Truth(1.0, 0.9), Evidence.unknown("none"))
    assert g.verdict is Verdict.UNKNOWN
    assert g.statement == STATEMENT
    assert g.truth == Truth(1.0, pytest.approx(0.75))


def test_correction_replaces_an_asserted_swap():
    g = combine(STATEMENT, Truth(1.0, 0.9), swap_evidence())
    assert g.verdict is Verdict.CORRECTED
    assert g.statement == CORRECT
    assert g.truth == Truth(1.0, 0.7)
    assert g.tier == ACT


def test_correction_ignored_when_llm_denies_the_statement():
    # "mammals are not dolphins" is right; the evidence agrees, nothing to correct
    g = combine(STATEMENT, Truth(0.0, 0.8), swap_evidence())
    assert g.verdict is Verdict.REFUTES
    assert g.statement == STATEMENT
    assert g.truth.f == pytest.approx(0.0)


def test_refuting_evidence_demotes_an_assertion():
    ev = Evidence(Verdict.REFUTES, Truth(0.0, 0.7), "wikidata", "closed world")
    g = combine(("-->", "whale", "fish"), Truth(1.0, 0.9), ev)
    assert g.tier == HYPOTHESIZE


def test_zero_confidence_on_both_sides_does_not_divide_by_zero():
    g = combine(STATEMENT, Truth(1.0, 0.1), Evidence.unknown("none"))
    assert g.truth.c == 0.0


def test_metta_rendering_is_parseable():
    from omega_grounding.nal import parse

    g = combine(STATEMENT, Truth(1.0, 0.9), swap_evidence())
    parsed = parse(g.to_metta())
    assert parsed[0] == "grounded" and parsed[1] == "CORRECTED"
    ev = parse(swap_evidence().to_metta())
    assert ev[3] == ("correction", CORRECT)
