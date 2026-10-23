from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from functools import reduce
from typing import Dict, List, Optional

from ..nal import ACT, INHERITANCE, Term, Truth, deduction, expectation, is_statement, normalize, reverse, tier
from .datasets import Chain, Item, _comparable


@dataclass(frozen=True)
class Final:
    """A premise after a pipeline has processed it."""

    statement: Term
    truth: Truth
    emitted: Term       # what the LLM wrote
    verdict: str = "-"  # grounded pipeline only


def _rate(num: int, den: int) -> Optional[float]:
    return num / den if den else None


def premise_metrics(items: Dict[str, Item], finals: Dict[str, Final]) -> Dict[str, Optional[float]]:
    graded = act_true = act_false = n_true = n_false = correct = 0
    brier = 0.0
    swapped = swapped_act = 0
    for item_id, fin in finals.items():
        item = items[item_id]
        if item.swappable and normalize(fin.emitted) == normalize(reverse(item.statement)):
            swapped += 1
            if normalize(fin.statement) == normalize(fin.emitted) and tier(fin.truth) == ACT and fin.truth.f >= 0.5:
                swapped_act += 1
        truth = item.truth_of(fin.statement)
        if truth is None:
            continue
        graded += 1
        act = tier(fin.truth) == ACT
        brier += (expectation(fin.truth) - (1.0 if truth else 0.0)) ** 2
        correct += (fin.truth.f >= 0.5) == truth
        if truth:
            n_true += 1
            act_true += act
        else:
            n_false += 1
            act_false += act
    return {
        "false_act_rate": _rate(act_false, n_false),
        "true_act_rate": _rate(act_true, n_true),
        "act_precision": _rate(act_true, act_true + act_false),
        "belief_accuracy": _rate(correct, graded),
        "brier": brier / graded if graded else None,
        "swapped_act_rate": _rate(swapped_act, swapped),
        "ungradable": float(len(finals) - graded),
    }


def _chain_conclusion(premises: List[Final], conclusion: Term) -> Optional[Truth]:
    """Deduce along (A-->B), (B-->C), ... if the statements actually link up."""
    statements = [normalize(p.statement) for p in premises]
    if not all(is_statement(s, INHERITANCE) for s in statements):
        return None
    for left, right in zip(statements, statements[1:]):
        if left[2] != right[1]:
            return None
    if (INHERITANCE, statements[0][1], statements[-1][2]) != normalize(conclusion):
        return None
    return reduce(deduction, [p.truth for p in premises])


def chain_metrics(chains: List[Chain], finals: Dict[str, Final]) -> Dict[str, Optional[float]]:
    act_true = act_false = n_true = n_false = derived_true = 0
    confidence_true = 0.0
    for chain in chains:
        if not all(p in finals for p in chain.premises):
            continue
        truth = _chain_conclusion([finals[p] for p in chain.premises], chain.conclusion)
        act = truth is not None and tier(truth) == ACT
        if chain.gold:
            n_true += 1
            act_true += act
            if truth is not None:
                derived_true += 1
                confidence_true += truth.c
        else:
            n_false += 1
            act_false += act
    return {
        "chain_false_act_rate": _rate(act_false, n_false),
        "chain_true_act_rate": _rate(act_true, n_true),
        "chain_true_mean_confidence": confidence_true / derived_true if derived_true else None,
    }


def verdict_counts(finals: Dict[str, Final]) -> Dict[str, int]:
    return dict(Counter(f.verdict for f in finals.values()))


def formulation_counts(items: Dict[str, Item], emitted: Dict[str, Final]) -> Dict[str, int]:
    """Classify what the LLM wrote for each item, before any grounding."""
    counts = Counter()
    for item_id, fin in emitted.items():
        item = items[item_id]
        n = normalize(fin.emitted)
        if n == normalize(item.statement):
            counts["canonical"] += 1
        elif _comparable(fin.emitted) == _comparable(item.statement):
            counts["equivalent"] += 1
        elif item.swappable and n == normalize(reverse(item.statement)):
            counts["swapped"] += 1
        elif item.exclusive and item.truth_of(fin.emitted) is False:
            counts["wrong_value"] += 1  # well-formed answer, factually wrong
        else:
            counts["other"] += 1
        truth = item.truth_of(fin.emitted)
        if truth is not None:
            counts["belief_graded"] += 1
            counts["belief_correct"] += (fin.truth.f >= 0.5) == truth
    return dict(counts)
