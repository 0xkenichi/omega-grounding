# Draft issue for singnet/Omega

> Not posted. Edit, then open it at https://github.com/singnet/Omega/issues before sending a PR.

**Title:** Proposal: automated premise grounding plugin + benchmark against reference-failure-modes.md

**Body:**

`docs/reference-failure-modes.md` identifies premise formulation as Omega's primary failure surface: LLM-supplied facts are right ~55% of the time, asymmetric relations get swapped up to 16.6% of the time, LLM confidence runs ~15 points high, and the formal engine cannot detect any of it. `tutorial-07-grounded-reasoning.md` names automated retrieval with programmatic source-to-confidence mapping as the longer-term direction, with the manual pattern as "the bridge until that automation exists".

I have a working prototype of that automation as a plugin, using the existing plugin API (`loadOmegaPlugin`, `add-skill`, `add-prompt-extension`, `configure`, `remember`):

- **`ground` skill.** The agent passes a premise exactly as it would pass it to `|-`. The plugin looks the statement up in an external source, and returns the premise to use, with provenance and the ACT/HYPOTHESIZE/IGNORE tier from `reference-orchestration.md`.
- **Calibration uses Omega's own math.** LLM confidence is discounted by the measured overconfidence, then merged with source evidence through `Truth_Revision` from `lib_nal.metta`. Source confidence follows tutorial-07's table (primary 0.9, verified secondary 0.7, ...).
- **Swaps and wrong values are corrected**, not just down-weighted. `(--> mammal dolphin)` comes back as `(--> dolphin mammal)` with verdict `CORRECTED`; `(--> (× usdc 18) decimals)` comes back as `(--> (× usdc 6) decimals)`.
- **Sources so far:** Wikidata (class and taxon trees, walked through the entity API because WDQS is frequently rate-limited) and Ethereum state over JSON-RPC (contract code, EIP-1967/OpenZeppelin proxy slots, ERC-20 decimals/symbol). Sources are a small interface, so SEC EDGAR, PubMed, etc. can be added.
- **Benchmark** that scores three pipelines on identical LLM premises (as written / minus 15 points / grounded) on: false premises reaching ACT, true premises reaching ACT, swaps still acted on, Brier score, and false multi-hop conclusions reaching ACT. Sources are recorded to a cassette, so it runs offline and in CI. Premises come from a seeded noise model at the rates in `reference-failure-modes.md`, or from a real LLM.

Verified on SWI-Prolog 10.0.2, PeTTa v1.0.4 and current `main`. The plugin loads through `loadMettaPlugin`, and a parity test checks the MeTTa rule against the Python implementation the benchmark uses. In 3 sessions of the real `(omega)` loop with ASI:One, the agent called `ground` unprompted and answered 9/9 questions correctly. Both token answers were corrected from the chain, where `asi1` alone says 18. While integrating I hit a duplicate-definition bug in `(library Omega ...)` imports that also affects `openclaw`; it is written up separately.

Measured on a real model, ASI:One `asi1` (one of Omega's own providers), over 151 items:
- **Textbook facts:** the model is already right, and grounding changes nothing.
- **Long-tail facts** (ERC-20 decimals): the model was wrong on 28 of 83 and would have acted on 27 of them. Grounding corrected all 28 from the chain, so false premises reaching ACT went from 96% to 0% and belief accuracy from 66% to 100%.
- **Omega's manual −15-point discount** reduced false ACT on these only to 64%, and it cannot correct a value.

Questions before I open a PR:

1. Would you take this as a plugin under `plugins/grounding`, or prefer it maintained externally?
2. The Python logic is currently a pip-installable package that the plugin's `.py` imports. Should it be vendored into the plugin directory instead?
3. Should the benchmark live under `Autotests/` or stay separate (it is not an agent-loop test)?
4. Is there an existing set of premises from the Max Botnick runs that the benchmark could use, instead of or alongside the synthetic noise model?

Results and code: https://github.com/0xkenichi/omega-grounding
