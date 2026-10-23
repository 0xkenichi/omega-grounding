"""Run the grounding benchmark.

    omega-ground-bench                          # replay recorded sources, synthetic LLM
    omega-ground-bench --transport record       # refresh the cassette from live sources
    omega-ground-bench --llm claude --transport record   # real LLM premises (API cost)
    omega-ground-bench --llm ollama --model qwen2.5:7b --transport record   # local model, no key
    ASIONE_API_KEY=... omega-ground-bench --llm asione --transport record    # ASI:One
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
from .llm import PROFILES, CachedLLM, ClaudeAtomizer, NoiseModel, OllamaAtomizer, OpenAICompatAtomizer, SyntheticLLM
from .metrics import Final, chain_metrics, formulation_counts, premise_metrics, verdict_counts

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


def formulation_markdown(counts: Dict[str, int], n_items: int) -> str:
    """How the LLM wrote each premise: the failure surface Omega's report measures."""
    rows = [("Canonical statement", "canonical"), ("Equivalent phrasing (e.g. smart_contract)", "equivalent"),
            ("Relation swapped", "swapped"), ("Well-formed answer with the wrong value", "wrong_value"),
            ("Other form (granularity, copula, naming)", "other"),
            ("Unparseable output", "unparseable"), ("Refused", "refused")]
    lines = ["### Premise formulation by the LLM", "", "| Outcome | Count | Share |", "|---|---|---|"]
    for label, key in rows:
        n = counts.get(key, 0)
        lines.append(f"| {label} | {n} | {n / n_items:.1%} |")
    believed = counts.get("belief_correct", 0), counts.get("belief_graded", 0)
    if believed[1]:
        lines += ["", f"Factual belief correct on {believed[0]} of {believed[1]} gradable premises "
                      f"({believed[0] / believed[1]:.1%})."]
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
    parser.add_argument("--domains", nargs="+", default=["taxonomy", "onchain", "onchain_longtail"])
    parser.add_argument("--llm", choices=["synthetic", "claude", "ollama", "asione"], default="synthetic")
    parser.add_argument("--profiles", nargs="+", choices=sorted(PROFILES), default=["omega-docs", "mild"])
    parser.add_argument("--factual-error-rate", type=float, help="custom synthetic profile")
    parser.add_argument("--swap-rate", type=float, help="custom synthetic profile")
    parser.add_argument("--seeds", type=int, default=30)
    parser.add_argument("--model", help="default: claude-opus-5-5 (claude), qwen2.5:7b (ollama), asi1 (asione; asi1-ultra needs a paid tier)")
    parser.add_argument("--ollama-url", default="http://127.0.0.1:11434")
    parser.add_argument("--effort", default="medium")
    parser.add_argument("--out", type=Path, default=ROOT / "benchmark" / "results")
    parser.add_argument("--premises", type=Path, help="real-LLM answer cache (default: OUT/premises.jsonl)")
    args = parser.parse_args(argv)

    if args.llm != "synthetic" and args.transport == "replay":
        parser.error(f"--llm {args.llm} writes new statements; use --transport record or live")

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
    if args.llm != "synthetic":
        if args.llm == "claude":
            llm = ClaudeAtomizer(args.model or "claude-opus-5-5", args.effort)
            title = f"LLM: {llm.name} (effort {args.effort})"
        elif args.llm == "asione":
            llm = OpenAICompatAtomizer(args.model or "asi1")
            title = f"LLM: {llm.name} (ASI:One, temperature 0)"
        else:
            llm = OllamaAtomizer(args.model or "qwen2.5:7b", args.ollama_url)
            title = f"LLM: {llm.name} (temperature 0)"
        llm = CachedLLM(llm, args.premises or args.out / "premises.jsonl")
        try:
            finals = run_pipelines(llm, items, grounder)
        finally:
            grounder.close()  # keep live lookups recorded so far
            llm.save()
        run = score(items, chains, finals)
        formulation = formulation_counts(items, finals["baseline"])
        formulation.update(refused=llm.refusals, unparseable=llm.unparseable)
        results[llm.name] = {"summary": summarize([run]), "formulation": formulation,
                             "premises": {i: {"emitted": fmt(f.emitted), "truth": str(f.truth),
                                              "grounded": fmt(finals["grounded"][i].statement),
                                              "verdict": finals["grounded"][i].verdict}
                                          for i, f in finals["baseline"].items()}}
        sections.append(to_markdown(title, summarize([run]), 1, verdict_counts(finals["grounded"])))
        sections.append(formulation_markdown(formulation, len(items)))
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
