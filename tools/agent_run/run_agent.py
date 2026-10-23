"""Run the real Omega agent loop with the grounding plugin and a live LLM, then stop it.

    ASIONE_API_KEY=... python tools/agent_run/run_agent.py --petta ~/omega-runtime/PeTTa

What runs is Omega's own run.metta -> lib_omega -> (omega) loop, unchanged, with:
  - LLM: ASI:One (Omega's ASIOne provider), model asi1
  - channel: a scripted chat (agentrun_channel) that plays script.json
  - plugins: the ASIOne provider, grounding, and agentrun_safety (removes shell, file,
    web, memory and raw-MeTTa skills because this is not sandboxed)
  - stand-ins (stubs/) for chromadb, ddgs and py_landlock, whose real packages are not
    installed; the skills that would use them are removed
Omega's config/plugins.yaml, config/config.yaml and memory/history.metta are swapped
for the run and restored afterwards. Outputs: transcript.jsonl, history.metta, omega.log in --out.
"""

import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

PLUGINS_YAML = """\
- name: agentrun_channel
  loader: python
  location: "{here}"

- name: asione
  loader: python
  location: "{{REPO}}/providers"

- name: grounding
  loader: metta
  location: "{{REPO}}/plugins/grounding"

- name: agentrun_safety
  loader: metta
  location: "{here}"
"""


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--petta", type=Path, required=True)
    parser.add_argument("--script", type=Path, default=HERE / "script.json")
    parser.add_argument("--out", type=Path, default=ROOT / "benchmark" / "results" / "agent-run")
    parser.add_argument("--model", default="asi1")
    parser.add_argument("--minutes", type=float, default=25)
    parser.add_argument("--loops", type=int, default=6, help="agent turns allowed after each message")
    args = parser.parse_args(argv)

    if not os.environ.get("ASIONE_API_KEY"):
        sys.exit("ASIONE_API_KEY is not set")
    petta = args.petta.resolve()
    omega = petta / "repos" / "Omega"
    plugins_yaml, history = omega / "config" / "plugins.yaml", omega / "memory" / "history.metta"
    config_yaml = omega / "config" / "config.yaml"
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    transcript = out / "transcript.jsonl"
    transcript.write_text("")
    n_messages = len(json.loads(args.script.read_text())["messages"])

    env = dict(os.environ)
    env.update({
        "PETTA_PATH": str(petta),
        "PYTHONPATH": os.pathsep.join([str(HERE / "stubs"), str(HERE), str(ROOT / "src")]),
        "AGENT_RUN_SCRIPT": str(args.script.resolve()),
        "AGENT_RUN_TRANSCRIPT": str(transcript),
        "OMEGA_provider": "ASIOne",
        "OMEGA_asione_model": args.model,
        "OMEGA_commchannel": "script",
        "OMEGA_embeddingprovider": "OpenAI",   # skips loading a local embedding model; memory skills are removed
        "OMEGA_groundingRemember": "disabled",
        "OMEGA_GROUNDING_MODE": "record",
        "OMEGA_GROUNDING_CASSETTE": str(ROOT / "benchmark" / "cassettes" / "sources.json"),
    })

    # Omega's policy names Docker paths (/PeTTa, /proc, ...); give the run one with local paths.
    # Landlock is stubbed on macOS, so this is informational; the file skills are removed.
    policy = out / "policy.yaml"
    policy.write_text(f"version: 1\nfilesystem_policy:\n  read_only:\n    - {petta}\n  read_write: []\n")
    env["OMEGA_securityPolicyPath"] = str(policy)

    shutil.copy2(plugins_yaml, out / "plugins.yaml.orig")
    shutil.copy2(history, out / "history.metta.orig")
    shutil.copy2(config_yaml, out / "config.yaml.orig")
    plugins_yaml.write_text(PLUGINS_YAML.format(here=HERE))
    # Numbers must come from YAML: environment overrides arrive as strings.
    config = config_yaml.read_text()
    config = re.sub(r"(?m)^maxNewInputLoops:.*$", f"maxNewInputLoops: {args.loops}", config)
    config = re.sub(r"(?m)^wakeupInterval:.*$", "wakeupInterval: 100000", config)  # no autonomous wake-ups
    config_yaml.write_text(config)
    history.write_text("")
    started = time.time()
    log = (out / "omega.log").open("w")
    proc = subprocess.Popen([sys.executable, str(ROOT / "tools" / "run_metta.py"), "run.metta"],
                            cwd=petta, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    reason = "timeout"
    try:
        while time.time() - started < args.minutes * 60:
            time.sleep(5)
            if proc.poll() is not None:
                reason = f"agent exited with code {proc.returncode}"
                break
            rows = [json.loads(line) for line in transcript.read_text().splitlines() if line.strip()]
            last_user = max((r["message_index"] for r in rows if r["role"] == "user"), default=-1)
            replies = [r for r in rows if r["role"] == "agent" and r["message_index"] == n_messages - 1]
            if last_user == n_messages - 1 and replies and time.time() - replies[-1]["t"] > 45:
                reason = "conversation finished"
                break
    finally:
        if proc.poll() is None:
            os.killpg(proc.pid, signal.SIGTERM)
            try:
                proc.wait(timeout=20)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
        log.close()
        shutil.copy2(history, out / "history.metta")
        for name, target in (("plugins.yaml", plugins_yaml), ("history.metta", history), ("config.yaml", config_yaml)):
            shutil.copy2(out / f"{name}.orig", target)
            (out / f"{name}.orig").unlink()
    print(f"stopped: {reason} after {time.time() - started:.0f}s; outputs in {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
