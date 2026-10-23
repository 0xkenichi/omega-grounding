# omega-grounding

Automated premise grounding for [Omega](https://github.com/singnet/Omega), SingularityNET's neural-symbolic agent, plus a benchmark that measures it against the failure modes Omega documents for itself.

## The problem

Omega's LLM turns language into NAL premises such as `((--> dolphin mammal) (stv 1.0 0.9))`, and its MeTTa reasoners (NAL `|-`, PLN `|~`) derive conclusions from them. Omega's own [failure-mode report](https://github.com/singnet/Omega/blob/main/docs/reference-failure-modes.md) finds that this first step is the main source of error:

- LLM-supplied facts are right about **55%** of the time.
- Asymmetric relations get **swapped** (`(--> mammal dolphin)`) up to **16.6%** of the time.
- LLM confidence runs about **15 points** too high.
- The formal engine "cannot detect these errors". It amplifies them with "mathematical authority".

[Tutorial 07](https://github.com/singnet/Omega/blob/main/docs/tutorial-07-grounded-reasoning.md) gives a manual fix: look the fact up in a trusted source, then set confidence by source quality. It names the automated version as the longer-term goal: "the bridge until that automation exists." This repository is that automation.

## What it does

A `ground` skill for the agent. The agent passes a premise as it would pass it to `|-`, and gets back the premise it should actually reason with:

```
ground "((--> mammal dolphin) (stv 1.0 0.9))"
→ (grounded CORRECTED ((--> dolphin mammal) (stv 1.0 0.7)) ACT
     "wikidata: only the reverse holds: Q7369 (dolphin) -> Q7377 (mammal)")

ground "((--> (× usdc 18) decimals) (stv 1.0 0.9))"
→ (grounded CORRECTED ((--> (× usdc 6) decimals) (stv 1.0 0.9)) ACT
     "ethereum: mainnet 0xa0b8…eb48.decimals() = 6")

ground "((--> weth ([] upgradeable)) (stv 1.0 0.8))"
→ (grounded REFUTES ((--> weth ([] upgradeable)) (stv 0.3171 0.8542)) HYPOTHESIZE
     "ethereum: mainnet 0xc02a…6cc2 no EIP-1967/OpenZeppelin proxy slot set")
```

How the returned premise is computed (`plugin/grounding/grounding_core.metta`, mirrored in `src/omega_grounding/evidence.py`):

1. **Discount.** The LLM's confidence is lowered by the 15 points Omega measured.
2. **Look up.** The statement goes to the first source that covers it. Confidence comes from the source class in tutorial 07: on-chain state is primary (0.9), Wikidata is verified secondary (0.7).
3. **Correct.** If the source affirms a different statement (a reversed relation, a different value) and the LLM was asserting, the premise is replaced with the correct one.
4. **Revise.** Otherwise the evidence is merged with Omega's own `Truth_Revision` from `lib_nal.metta`, exactly as `|-` merges two premises.
5. **Tier.** The result is labelled ACT / HYPOTHESIZE / IGNORE using the thresholds in `reference-orchestration.md`. With `groundingRemember` on, it is stored in long-term memory along with its provenance.

### Sources

| Source | Statements | Confidence |
|---|---|---|
| Ethereum JSON-RPC | `(--> X ([] contract))`, `(--> X ([] upgradeable))`, `(--> (× X N) decimals)`, `(--> (× X S) symbol)` | 0.9 (0.8 when no known proxy slot is set) |
| Wikidata entity API | `(--> A B)` between plain terms | 0.7; absence of a path also 0.7 (closed world: demotes LLM assertions made with confidence below ~0.93; `--open-world` to disable) |

Wikidata details that matter:

- **Every exact label match is a candidate sense.** "dolphin" matches a surname, a KDE app and an emulator before the animal. Senses that sit in a class or taxon tree are tried first.
- **Taxa follow parent-taxon links only.** Once the walk reaches a taxon, it ignores subclass links. Otherwise Wikidata's clade-mixing links make whales fish.
- **No SPARQL.** The walk uses the entity API in batches, because the query service is often rate-limited.

Adding a source means implementing `supports(statement)` and `check(statement) -> Evidence`; see `src/omega_grounding/sources/`.

## Benchmark

Three pipelines see identical LLM premises:

- **baseline**: the premise as the LLM wrote it.
- **discount**: Omega's manual mitigation, confidence minus 15 points.
- **grounded**: this plugin.

They are scored on:
- false premises that reach ACT;
- true premises that reach ACT;
- swapped relations still acted on;
- Brier score of the NAL expectation;
- false multi-hop conclusions (2–3 hop deduction chains) that reach ACT.

Inputs and how the numbers are produced:

- **Datasets** (`benchmark/datasets/`): 43 taxonomy claims, 24 Ethereum mainnet claims, 84 open questions about long-tail token decimals, and 12 chains. Taxonomy and well-known-token labels are by hand, independent of the sources, so source mistakes count against grounding. Long-tail labels come from the Uniswap token list and are confirmed on-chain, where the chain is the definition of the fact.
- **Premises** come from a seeded noise model at the rates in Omega's failure-mode report (`omega-docs`) and at milder rates (`mild`), or from a real LLM: `--llm asione` (ASI:One), `--llm ollama` (any local open-weights model, no key), or `--llm claude`. Real answers are cached with the prompt's hash, so reruns are free and reproducible.
- **Sources** are replayed from `benchmark/cassettes/sources.json`, recorded live, so results are reproducible offline.

```bash
pip install -e '.[dev]'
omega-ground-bench                         # replay, synthetic premises, 30 seeds per profile
omega-ground-bench --transport record      # refresh the recording from live sources
pip install -e '.[claude]'                 # Python >= 3.10
ASIONE_API_KEY=... omega-ground-bench --llm asione --transport record   # ASI:One (free tier: asi1)
omega-ground-bench --llm ollama --model qwen2.5:7b --transport record   # local model, no key
omega-ground-bench --llm claude --transport record   # Claude (API cost)
```

The `--llm claude` path uses `claude-opus-5-5` with structured JSON output. It opts into server-side refusal fallbacks (`fallbacks: "default"`), so a declined request is retried on a fallback model.

### Results

#### A real LLM: ASI:One (`asi1`)

ASI:One is the ASI Alliance's model and one of Omega's built-in providers. It ran at temperature 0 on all 151 items, a single deterministic run.

- Its answers are committed in [`benchmark/results/asione-asi1/premises.jsonl`](benchmark/results/asione-asi1/premises.jsonl).
- Full reports are in [`benchmark/results/asione-asi1/`](benchmark/results/asione-asi1/), one per dataset.

| ASI:One, by dataset | LLM facts right | False premises reaching ACT: as written → grounded | True premises reaching ACT: as written → grounded |
|---|---|---|---|
| Textbook taxonomy (43) | 41/41 (100%) | 0% → 0% | 100% → 100% |
| Well-known tokens (24) | 22/24 (92%) | 9.1% → **0%** | 84.6% → **92.3%** |
| Long-tail token decimals (84) | 55/83 (**66%**) | 96.4% → **0%** (all 28 corrected) | 96.4% → **100%** |
| All 151 | 118/148 (80%) | 53.8% → **0%** | 95.8% → **99.2%** |

What this shows:

- **On textbook facts the model is already right, so grounding has nothing to fix.** It costs a little calibration (Brier 0.006 → 0.016).
- **On long-tail facts the model guesses, and confidently.** It gave the wrong decimals for 28 of 83 tokens and would have acted on 27 of them. Grounding replaced every one with the on-chain value: belief accuracy rose from 66% to 100%, and Brier fell from 0.263 to 0.002.
- **No swapped relations.** The model wrote no swaps, and 4.6% of its premises used an equivalent phrasing (`smart_contract`, `uni_token_contract`) that the sources accept.
- **Omega's manual fix only partly works on real outputs.** The −15-point discount helps somewhat on the long tail (false ACT 96% → 64%) because the model's confidence there is spread out. It never corrects a value.

#### Synthetic premises (stress test)

A seeded noise model generates the premises; 30 seeds per profile. Sources are replayed from the committed recording. Full output: [`benchmark/results/report.md`](benchmark/results/report.md).

| Metric | `omega-docs` noise (45% factual error, 16.6% swaps): baseline → grounded | `mild` noise (10%, 5%): baseline → grounded |
|---|---|---|
| False premises reaching ACT ↓ | 0.475 → **0.025** | 0.137 → **0.003** |
| True premises reaching ACT ↑ | 0.554 → **0.906** | 0.906 → **0.943** |
| Belief accuracy ↑ | 0.548 → **0.932** | 0.898 → **0.962** |
| Brier score ↓ | 0.382 → **0.062** | 0.094 → **0.026** |
| Swapped relations still acted on ↓ | 0.516 → **0.026** | 0.565 → **0.013** |
| True multi-hop conclusions reaching ACT ↑ | 0.200 → **0.237** | **0.713** → 0.621 |

The `omega-docs` rates come from Omega's failure-mode report. As the ASI:One run shows, a real model's error rate depends heavily on the kind of fact: it ranges from 0% to 34% here.

#### Source accuracy

On the canonical statements, the sources agree with the labels on **145 of 151**:

- **No false claim is supported.**
- **All 84 long-tail decimals match the chain.** Those labels come from the Uniswap token list and were checked on-chain.
- **The 6 misses are all true claims:**
  - reptile → animal, dinosaur → reptile, insect → hexapod: Wikidata search does not return the taxa Reptilia and Hexapoda for these words.
  - oak → tree, iron → metal: the class path is longer than the hop limit.
  - stETH upgradeable: an Aragon proxy, which the slot check does not recognise.
- **Why the misses rarely cost anything with ASI:One:** its confidence on them is 0.95–0.99, and a closed-world refutation cannot pull that below ACT.

### Live agent run

This is Omega's real agent loop (`run.metta` → `lib_omega` → `(omega)`) with the plugin, ASI:One `asi1` as the LLM, and a scripted chat. It ran 3 times; scored in [`benchmark/results/agent-run/summary.md`](benchmark/results/agent-run/summary.md), with every session's transcript, Omega history and full log alongside.

- **9/9 answers correct.** The questions were DOVU decimals, EUROP decimals and "are whales fish?". The agent called `ground` unprompted before each answer.
- **Both token answers came back CORRECTED from the chain** (8 and 6), where ASI:One by itself says 18 for both.
- **The UNKNOWN reply lists the checkable shapes, and the agent used it** to rephrase a premise once and get it checked.
- **Grounding fixes facts, not arithmetic.** One session stated the right decimals and then multiplied wrongly.

How it was run (`tools/agent_run/`; reproduce with `python tools/agent_run/run_agent.py --petta /path/to/PeTTa` and an `ASIONE_API_KEY`):

- **On a Mac, without Omega's Linux sandbox.** A safety plugin removes every shell, file, web, memory and raw-MeTTa skill. A `nal` skill allows only whitelisted inference expressions (unit-tested against code smuggled into premises).
- **ChromaDB, ddgs and Landlock are replaced by stand-ins** (`tools/agent_run/stubs/`), because the real packages were too large to download here. Nothing that uses them stays enabled.

Integrating with the real loop exposed an Omega/PeTTa bug: plugin functions get defined two or more times, so `ground` returned up to 64 copies of its answer. The plugin now works around it. The write-up is in [`docs/UPSTREAM_BUGS.md`](docs/UPSTREAM_BUGS.md).

## Using it in Omega

For a manual PeTTa-based install (Omega pins **PeTTa v1.0.4**; newer PeTTa resolves relative imports differently and Omega's own tests fail on it):

```bash
sh plugin/install.sh /path/to/PeTTa/repos/Omega /path/to/PeTTa/.venv
```

This installs the package into Omega's Python environment, links `plugin/grounding` into `Omega/plugins/`, and registers it in `config/plugins.yaml`. Configuration:

- `OMEGA_groundingEnabled`: `enabled` or `disabled`.
- `OMEGA_groundingLlmDiscount`: default `0.15`.
- `OMEGA_groundingRemember`: `enabled` or `disabled`.
- `OMEGA_GROUNDING_RPC_URL`: Ethereum JSON-RPC endpoint (default `https://ethereum-rpc.publicnode.com`).

Run the MeTTa tests against a real runtime:

```bash
PETTA_PATH=/path/to/PeTTa OMEGA_PATH=/path/to/PeTTa/repos/Omega pytest tests/test_metta_parity.py tests/test_omega_plugin.py
```

**macOS without admin rights.** The SWI-Prolog app's built-in Python bridge expects the system-wide python.org Python 3.11. Without it, host Prolog from Python instead:

```bash
pip install janus-swi pyyaml   # in a venv, with the app's swipl on PATH
```

Then run MeTTa files through `tools/run_metta.py` instead of PeTTa's `run.sh`. Point the tests at it with `PETTA_RUN`, set to a shell script that execs it.

Try a single premise without Omega:

```bash
omega-ground "((--> mammal dolphin) (stv 1.0 0.9))"
```

## Status

- **Python library, sources and benchmark: working.** Unit tests pass offline, and the benchmark runs against recorded live data.
- **MeTTa plugin: loads and runs inside Omega.** Verified on SWI-Prolog 10.0.2, PeTTa v1.0.4 and Omega at commit 63a7826.
  - `tests/test_omega_plugin.py` loads the plugin through Omega's own `loadMettaPlugin`. Config, skill registration and the prompt extension all go through Omega's APIs. It then calls `ground` and gets the correct grounded premises.
  - `tests/test_metta_parity.py` shows the MeTTa and Python grounding rules agree on verdict, statement, truth and tier.
  - Both tests skip unless `PETTA_PATH` and `OMEGA_PATH` are set.
- **Full agent run: done** (see Live agent run). Still not exercised: `groundingRemember`, which needs Omega's ChromaDB memory stack.
- **The synthetic noise model is a stress model.** Its rates come from Omega's report, but it does not stand in for any particular LLM. The ASI:One run measures a real one.
- **Known source limitations, listed under Results:** 6 true claims are missed.
- **Live Wikidata lookups are slow:** up to a few minutes per new claim. They are instant once recorded.

## Upstream

`docs/PROPOSAL.md` is a draft issue for singnet/Omega asking how the maintainers would like to take this in.

## License

Apache-2.0, matching Omega.
