"""Score agent-run sessions: was each question answered, correctly, and how was `ground` used?

    python tools/agent_run/summarize.py benchmark/results/agent-run

Reads run-*/transcript.jsonl and run-*/omega.log; expected answers are regexes in
script.json ("expect"). Writes summary.md next to the runs.
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ANSI = re.compile(r"\x1b\[[0-9;]*m")
CALL = re.compile(r"COMMAND_RETURN: \(\((\w[\w-]*) (.*)")


def tool_calls(log_text):
    calls = []
    for name, rest in CALL.findall(ANSI.sub("", log_text)):
        if name == "quote":  # the loop's own source line echoed by PeTTa
            continue
        verdict = re.search(r"\(grounded (\w+) ", rest)
        calls.append((name, verdict.group(1) if verdict else None, rest[:160]))
    return calls


def score_run(run: Path, script: dict):
    rows = [json.loads(line) for line in (run / "transcript.jsonl").read_text().splitlines() if line.strip()]
    answers = []
    for i, (question, expect) in enumerate(zip(script["messages"], script["expect"])):
        replies = [r["text"] for r in rows if r["role"] == "agent" and r["message_index"] == i]
        reply = replies[-1] if replies else None
        correct = bool(reply and re.search(expect, reply, re.IGNORECASE))
        answers.append({"question": question, "reply": reply, "correct": correct})
    return answers, tool_calls((run / "omega.log").read_text())


def main(root: str) -> None:
    root = Path(root)
    script = json.loads((HERE / "script.json").read_text())
    runs = sorted(p for p in root.glob("run-*") if (p / "transcript.jsonl").exists())
    lines = ["# Agent runs: Omega + grounding plugin + ASI:One (asi1)", "",
             f"{len(runs)} session(s) of the real Omega loop; script in tools/agent_run/script.json.", ""]
    totals = Counter()
    for run in runs:
        answers, calls = score_run(run, script)
        grounds = [c for c in calls if c[0] == "ground"]
        verdicts = Counter(v for _, v, _ in grounds)
        lines += [f"## {run.name}", "",
                  f"Tool calls: {dict(Counter(c[0] for c in calls))}. "
                  f"`ground` verdicts: {dict(verdicts)}.", "",
                  "| Question | Answer given | Correct |", "|---|---|---|"]
        for a in answers:
            reply = (a["reply"] or "(no answer)").replace("|", "/").replace("\n", " ")[:160]
            lines.append(f"| {a['question'][:70]}… | {reply} | {'yes' if a['correct'] else 'no'} |")
            totals["questions"] += 1
            totals["answered"] += a["reply"] is not None
            totals["correct"] += a["correct"]
        totals["ground_calls"] += len(grounds)
        totals["unknown"] += verdicts.get("UNKNOWN", 0)
        lines.append("")
    lines.insert(4, f"**Overall:** {totals['correct']}/{totals['questions']} correct, "
                    f"{totals['answered']}/{totals['questions']} answered; "
                    f"{totals['ground_calls']} `ground` calls, {totals['unknown']} UNKNOWN.\n")
    (root / "summary.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else str(HERE.parents[1] / "benchmark" / "results" / "agent-run"))
