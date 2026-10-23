import pytest

from omega_grounding.nal import (
    ACT, HYPOTHESIZE, IGNORE, ParseError, Truth, deduction, fmt, parse, parse_premise,
    reverse, revision, tier,
)


def test_parse_roundtrip():
    text = "((--> (× usdc 6) decimals) (stv 1.0 0.9))"
    assert fmt(parse(text)) == text


def test_parse_premise_with_and_without_truth():
    statement, truth = parse_premise("((--> dolphin mammal) (stv 1.0 0.9))")
    assert statement == ("-->", "dolphin", "mammal")
    assert truth == Truth(1.0, 0.9)
    assert parse_premise("(--> dolphin mammal)") == (("-->", "dolphin", "mammal"), None)


@pytest.mark.parametrize("bad", ["(--> a b", "(--> a b))", "(a) (b)", '("unterminated)'])
def test_parse_rejects_malformed(bad):
    with pytest.raises(ParseError):
        parse(bad)


def test_reverse():
    assert reverse(("-->", "mammal", "dolphin")) == ("-->", "dolphin", "mammal")


def test_deduction_matches_lib_nal():
    # Truth_Deduction: f = f1 f2, c = f1 f2 c1 c2
    t = deduction(Truth(1.0, 0.9), Truth(1.0, 0.9))
    assert t.f == pytest.approx(1.0) and t.c == pytest.approx(0.81)


def test_revision_matches_lib_nal_including_clamps():
    # w1 = 0.75/0.25 = 3, w2 = 0.7/0.3 = 2.333; f = 3/5.333; c = 5.333/6.333
    t = revision(Truth(1.0, 0.75), Truth(0.0, 0.7))
    assert t.f == pytest.approx(0.5625)
    assert t.c == pytest.approx(0.8421, abs=1e-4)
    # Omega clamps confidence to max(c, c1, c2) and at most 0.99
    assert revision(Truth(1.0, 0.99), Truth(1.0, 0.99)).c == pytest.approx(0.99)


def test_tiers():
    assert tier(Truth(1.0, 0.5)) == ACT
    assert tier(Truth(0.6, 0.49)) == HYPOTHESIZE
    assert tier(Truth(0.3, 0.2)) == HYPOTHESIZE
    assert tier(Truth(0.0, 0.9)) == IGNORE
