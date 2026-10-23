from pathlib import Path

import pytest

from omega_grounding.bench.datasets import load_chains, load_items
from omega_grounding.bench.harness import MODES, prime, run_pipelines, score
from omega_grounding.bench.llm import PROFILES, SyntheticLLM
from omega_grounding.bench.metrics import Final, chain_metrics, premise_metrics
from omega_grounding.grounder import default_grounder
from omega_grounding.nal import Truth, parse
from omega_grounding.transport import CassetteMiss

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "benchmark" / "datasets"
CASSETTE = ROOT / "benchmark" / "cassettes" / "sources.json"


def test_datasets_load_and_chains_resolve():
    items = load_items(DATA, ["taxonomy", "onchain"])
    chains = load_chains(DATA, items)
    assert len(items) == 67 and len(chains) == 12
    assert items["t01"].truth_of(parse("(--> mammal dolphin)")) is False
    assert items["o12"].truth_of(parse("(--> (× USDC 6) decimals)")) is True


def test_synthetic_llm_is_seeded():
    items = load_items(DATA, ["taxonomy"])
    a = [SyntheticLLM(PROFILES["omega-docs"], 7).premise(i) for i in items.values()]
    b = [SyntheticLLM(PROFILES["omega-docs"], 7).premise(i) for i in items.values()]
    assert a == b


def test_premise_metrics_counts_false_act():
    items = load_items(DATA, ["taxonomy"])
    finals = {
        "t01": Final(parse("(--> dolphin mammal)"), Truth(1.0, 0.8), parse("(--> dolphin mammal)")),
        "f01": Final(parse("(--> whale fish)"), Truth(1.0, 0.8), parse("(--> whale fish)")),
    }
    m = premise_metrics(items, finals)
    assert m["false_act_rate"] == 1.0 and m["true_act_rate"] == 1.0 and m["act_precision"] == 0.5


def test_chain_needs_linked_premises():
    items = load_items(DATA, ["taxonomy"])
    chains = [c for c in load_chains(DATA, items) if c.id == "c01"]
    linked = {"t01": Final(parse("(--> dolphin mammal)"), Truth(1.0, 0.9), parse("(--> dolphin mammal)")),
              "t11": Final(parse("(--> mammal animal)"), Truth(1.0, 0.9), parse("(--> mammal animal)"))}
    assert chain_metrics(chains, linked)["chain_true_act_rate"] == 1.0
    swapped = dict(linked, t01=Final(parse("(--> mammal dolphin)"), Truth(1.0, 0.9), parse("(--> mammal dolphin)")))
    assert chain_metrics(chains, swapped)["chain_true_act_rate"] == 0.0


@pytest.mark.skipif(not CASSETTE.exists(), reason="no recorded cassette")
def test_grounding_reduces_false_act_on_recorded_sources():
    """The headline claim, checked offline against the committed recording."""
    items = load_items(DATA, ["taxonomy", "onchain"])
    chains = load_chains(DATA, items)
    grounder = default_grounder(CASSETTE, "replay")
    try:
        prime(grounder, items)
    except CassetteMiss as exc:
        pytest.skip(f"cassette incomplete: {exc}")
    runs = [score(items, chains, run_pipelines(SyntheticLLM(PROFILES["omega-docs"], s), items, grounder))
            for s in range(10)]
    mean = {m: sum(r[m]["false_act_rate"] for r in runs) / len(runs) for m in MODES}
    assert mean["grounded"] < mean["discount"] <= mean["baseline"]


def test_exclusive_items_grade_other_values_false():
    items = load_items(DATA, ["onchain_longtail"])
    item = next(iter(items.values()))
    _, (_, symbol, value), relation = item.statement
    other = str(int(value) + 1)
    assert item.truth_of(item.statement) is True
    assert item.truth_of(("-->", ("×", symbol, other), relation)) is False
    assert item.truth_of(("-->", ("×", symbol.upper(), value), relation)) is True
