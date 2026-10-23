"""Run the grounding benchmark.

    omega-ground-bench                          # replay recorded sources, synthetic LLM
    omega-ground-bench --transport record       # refresh the cassette from live sources
    omega-ground-bench --llm claude --transport record   # real LLM premises (API cost)
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Dict, List

from ..evidence import DEFAULT_LLM_DISCOUNT, discount
from ..grounder import Grounder, default_grounder
from ..nal import fmt, reverse
from .datasets import Chain, Item, load_chains, load_items
from .llm import PROFILES, ClaudeAtomizer, NoiseModel, SyntheticLLM
from .metrics import Final, chain_metrics, premise_metrics, verdict_counts

ROOT = Path(__file__).resolve().parents[3]
MODES = ("baseline", "discount", "grounded")
METRICS = [
    ("false_act_rate", "False premises reaching ACT", "lower"),
    ("true_act_rate", "True premises reaching ACT", "higher"),
    ("act_precision", "Precision of ACT premises", "higher"),
    ("belief_accuracy", "Belief accuracy (f >= 0.5 matches truth)", "higher"),
    ("brier", "Brier score of NAL expectation", "lower"),
    ("swapped_act_rate", "Swapped relations still acted on", "lower"),
    ("chain_false_act_rate", "False multi-hop conclusions reaching ACT", "lower"),
    ("chain_true_act_rate", "True multi-hop conclusions reaching ACT", "higher"),
    ("chain_true_mean_confidence", "Mean confidence of true conclusions", "higher"),
]


def prime(grounder: Grounder, items: Dict[str, Item]) -> None:
    """Look up every statement any seed can emit, so one recording replays for all."""
    for item in items.values():
        grounder.evidence(item.statement)
        if item.swappable:
            grounder.evidence(reverse(item.statement))


def run_pipelines(llm, items: Dict[str, Item], grounder: Grounder) -> Dict[str, Dict[str, Final]]:
    out: Dict[str, Dict[str, Final]] = {m: {} for m in MODES}
    for item_id, item in items.items():
        premise = llm.premise(item)
        if premise is None:
            continue
        statement, truth = premise
        out["baseline"][item_id] = Final(statement, truth, statement)
        out["discount"][item_id] = Final(statement, discount(truth, DEFAULT_LLM_DISCOUNT), statement)
        g = grounder.ground(statement, truth)
        out["grounded"][item_id] = Final(g.statement, g.truth, statement, g.verdict.value)
    return out


def score(items, chains, finals) -> Dict[str, dict]:
    return {mode: {**premise_metrics(items, f), **chain_metrics(chains, f)} for mode, f in finals.items()}


def summarize(runs: List[Dict[str, dict]]) -> Dict[str, dict]:
    summary: Dict[str, dict] = {}
    for mode in MODES:
        summary[mode] = {}
        for key, _, _ in METRICS:
            values = [r[mode][key] for r in runs if r[mode].get(key) is not None]
            if values:
                summary[mode][key] = {
                    "mean": statistics.fmean(values),
                    "sd": statistics.stdev(values) if len(values) > 1 else 0.0,
                }
    return summary


def to_markdown(title: str, summary: Dict[str, dict], n_runs: int, verdicts: Dict[str, int]) -> str:
    lines = [f"### {title}", "", f"{n_runs} run(s). Mean ± sd across runs.", "",
             "| Metric | Better | " + " | ".join(MODES) + " |",
             "|---|---|" + "---|" * len(MODES)]
    for key, label, better in METRICS:
        cells = []
        for mode in MODES:
            stat = summary[mode].get(key)
            cells.append("n/a" if stat is None else
                         f"{stat['mean']:.3f}" + (f" ± {stat['sd']:.3f}" if n_runs > 1 else ""))
        lines.append(f"| {label} | {better} | " + " | ".join(cells) + " |")
    if verdicts:
        lines += ["", "Grounded verdicts (all runs): " +
                  ", ".join(f"{k} {v}" for k, v in sorted(verdicts.items()))]
    return "\n".join(lines) + "\n"


def coverage_table(grounder: Grounder, items: Dict[str, Item]) -> str:
    """How the sources judged each canonical statement, against the gold label."""
    lines = ["### Source coverage on canonical statements", "",
             "| Item | Statement | Gold | Verdict | Source agrees |", "|---|---|---|---|---|"]
    agree = disagree = unknown = 0
    for item in items.values():
        ev = grounder.evidence(item.statement)
        if ev.verdict.value == "UNKNOWN":
            mark, unknown = "unknown", unknown + 1
        elif (ev.verdict.value == "SUPPORTS") == item.gold:
            mark, agree = "yes", agree + 1
        else:
            mark, disagree = "**no**", disagree + 1
        lines.append(f"| {item.id} | `{fmt(item.statement)}` | {item.gold} | {ev.verdict.value} | {mark} |")
    lines.insert(2, f"Agrees {agree}, disagrees {disagree}, unknown {unknown}.\n")
    return "\n".join(lines) + "\n"


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--transport", choices=["replay", "record", "live"], default="replay")
    parser.add_argument("--cassette", type=Path, default=ROOT / "benchmark" / "cassettes" / "sources.json")
    parser.add_argument("--datasets", type=Path, default=ROOT / "benchmark" / "datasets")
    parser.add_argument("--domains", nargs="+", default=["taxonomy", "onchain"])
    parser.add_argument("--llm", choices=["synthetic", "claude"], default="synthetic")
    parser.add_argument("--profiles", nargs="+", choices=sorted(PROFILES), default=["omega-docs", "mild"])
    parser.add_argument("--factual-error-rate", type=float, help="custom synthetic profile")
    parser.add_argument("--swap-rate", type=float, help="custom synthetic profile")
    parser.add_argument("--seeds", type=int, default=30)
    parser.add_argument("--model", default="claude-opus-5-5")
    parser.add_argument("--effort", default="medium")
    parser.add_argument("--out", type=Path, default=ROOT / "benchmark" / "results")
    args = parser.parse_args(argv)

    if args.llm == "claude" and args.transport == "replay":
        parser.error("--llm claude writes new statements; use --transport record or live")

    items = load_items(args.datasets, args.domains)
    chains = load_chains(args.datasets, items)
    grounder = default_grounder(args.cassette, args.transport)
    if args.transport != "replay":
        prime(grounder, items)
        grounder.close()

    profiles = {p: PROFILES[p] for p in args.profiles}
    if args.factual_error_rate is not None or args.swap_rate is not None:
        profiles = {"custom": NoiseModel(args.factual_error_rate or 0.0, args.swap_rate or 0.0)}

    sections = [f"# Grounding benchmark\n\nItems: {len(items)} ({', '.join(args.domains)}), "
                f"chains: {len(chains)}. Sources: {args.transport} ({args.cassette.name}).\n"]
    results = {}
    if args.llm == "claude":
        llm = ClaudeAtomizer(args.model, args.effort)
        finals = run_pipelines(llm, items, grounder)
        run = score(items, chains, finals)
        results[llm.name] = {"summary": summarize([run]), "refusals": llm.refusals,
                             "unparseable": llm.unparseable}
        sections.append(to_markdown(f"LLM: {llm.name} (effort {args.effort})", summarize([run]), 1,
                                    verdict_counts(finals["grounded"])))
    else:
        for name, noise in profiles.items():
            runs, verdicts = [], {}
            for seed in range(args.seeds):
                finals = run_pipelines(SyntheticLLM(noise, seed), items, grounder)
                runs.append(score(items, chains, finals))
                for k, v in verdict_counts(finals["grounded"]).items():
                    verdicts[k] = verdicts.get(k, 0) + v
            summary = summarize(runs)
            results[name] = {"noise": noise.__dict__, "summary": summary}
            sections.append(to_markdown(
                f"Synthetic LLM, profile `{name}` (factual error {noise.factual_error_rate}, "
                f"swap {noise.swap_rate})", summary, len(runs), verdicts))
    sections.append(coverage_table(grounder, items))
    grounder.close()

    report = "\n".join(sections)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "report.md").write_text(report)
    (args.out / "results.json").write_text(json.dumps(results, indent=2) + "\n")
    print(report)


if __name__ == "__main__":
    main()
