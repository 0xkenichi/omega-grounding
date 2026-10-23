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

- **Datasets** (`benchmark/datasets/`): 43 taxonomy claims, 24 Ethereum mainnet claims, and 12 chains. Ground truth is labelled by hand, independent of the sources, so source mistakes count against grounding.
- **Premises** come from a seeded noise model at the rates in Omega's failure-mode report (`omega-docs`) and at milder rates (`mild`), or from a real LLM with `--llm claude`.
- **Sources** are replayed from `benchmark/cassettes/sources.json`, recorded live, so results are reproducible offline.

```bash
pip install -e '.[dev]'
omega-ground-bench                         # replay, synthetic premises, 30 seeds per profile
omega-ground-bench --transport record      # refresh the recording from live sources
pip install -e '.[claude]'                 # Python >= 3.10
omega-ground-bench --llm claude --transport record   # real premises from Claude (API cost)
```

The `--llm claude` path uses `claude-opus-5-5` with structured JSON output. It opts into server-side refusal fallbacks (`fallbacks: "default"`), so a declined request is retried on a fallback model.

### Results

From `omega-ground-bench` (30 seeds per profile, sources replayed from the committed recording; full output in [`benchmark/results/report.md`](benchmark/results/report.md)).

Synthetic premises at **Omega's measured failure rates** (`omega-docs`: 45% factual error, 16.6% swaps):

| Metric | baseline | discount (−15 pts) | grounded |
|---|---|---|---|
| False premises reaching ACT ↓ | 0.475 | 0.475 | **0.025** |
| True premises reaching ACT ↑ | 0.563 | 0.563 | **0.718** |
| Precision of ACT premises ↑ | 0.595 | 0.595 | **0.980** |
| Belief accuracy ↑ | 0.546 | 0.546 | **0.846** |
| Brier score of NAL expectation ↓ | 0.383 | 0.333 | **0.109** |
| Swapped relations still acted on ↓ | 0.516 | 0.516 | **0.026** |
| False multi-hop conclusions reaching ACT ↓ | 0.075 | 0.008 | **0.000** |
| True multi-hop conclusions reaching ACT ↑ | 0.200 | 0.058 | **0.237** |

Synthetic premises from a **strong model on easy facts** (`mild`: 10% factual error, 5% swaps):

| Metric | baseline | discount | grounded |
|---|---|---|---|
| False premises reaching ACT ↓ | 0.137 | 0.137 | **0.003** |
| True premises reaching ACT ↑ | **0.899** | **0.899** | 0.828 |
| Precision of ACT premises ↑ | 0.910 | 0.910 | **0.998** |
| Brier score ↓ | 0.105 | 0.106 | **0.051** |
| Swapped relations still acted on ↓ | 0.565 | 0.565 | **0.013** |
| True multi-hop conclusions reaching ACT ↑ | **0.713** | 0.146 | 0.621 |

How to read this:

- **Grounding nearly eliminates acting on false or swapped premises at both noise levels.**
- **The cost shows with a strong LLM.** Some true facts drop out of ACT, because the sources miss 6 of 67 true claims (table below) and the closed-world rule then demotes them.
- **The −15-point discount does not move premises between tiers.** LLM confidences of 0.70–0.95 stay above the ACT threshold of 0.5 after the discount. It only bites on multi-hop chains, where it suppresses true and false conclusions alike.
- **The synthetic results are not a measurement of a real LLM.** Run `--llm claude` for that.

Source agreement with the hand labels on the canonical statements: **61 of 67**, with **no false claim supported**. The misses are all true claims:

- **reptile → animal, dinosaur → reptile, insect → hexapod:** Wikidata search does not return the taxa Reptilia and Hexapoda for these words.
- **oak → tree, iron → metal:** the class path is longer than the hop limit.
- **stETH upgradeable:** an Aragon proxy, which the slot check does not recognise.

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
- **Not yet exercised: a full agent run with an LLM choosing to call `ground`,** and `groundingRemember` (which needs Omega's ChromaDB memory stack).
- **The synthetic noise model is a stress model.** Its rates come from Omega's report, but it does not stand in for any particular LLM. Use `--llm claude` to measure a real one.
- **Known source limitations, listed under Results:** 6 true claims are missed.
- **Live Wikidata lookups are slow:** up to a few minutes per new claim. They are instant once recorded.

## Upstream

`docs/PROPOSAL.md` is a draft issue for singnet/Omega asking how the maintainers would like to take this in.

## License

Apache-2.0, matching Omega.
