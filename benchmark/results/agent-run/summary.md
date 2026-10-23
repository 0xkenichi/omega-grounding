# Agent runs: Omega + grounding plugin + ASI:One (asi1)

3 session(s) of the real Omega loop; script in tools/agent_run/script.json.

**Overall:** 9/9 correct, 9/9 answered; 10 `ground` calls, 1 UNKNOWN.

## run-1

Tool calls: {'ground': 4, 'pin': 2, 'send': 3}. `ground` verdicts: {'UNKNOWN': 1, 'CORRECTED': 2, 'SUPPORTS': 1}.

| Question | Answer given | Correct |
|---|---|---|
| I'm about to send a payment in DOVU, the ERC-20 token at 0x2aeAbde1aB7… | DOVU (0x2aeAbde1aB736c59E9A19BeD67681869eEF39526) uses 8 decimals, not the ERC-20 default 18. Raw amount = human amount × 10^8. E.g. 25 DOVU → 2500000000. | yes |
| Same question for Schuman EUR P (EUROP) at 0x888883b5F5D21fb10Dfeb70e8… | Schuman EUR P (EUROP, 0x888883b5F5D21fb10Dfeb70e8f9722B9FB0E5E51) uses 6 decimals. Raw amount = EUR amount × 10^6. E.g. 25 EUROP → 25000000. | yes |
| Different topic: are whales fish?… | No — whales are mammals, not fish (grounded via Wikidata: Q1865281 → mammal). They breathe air, are warm-blooded, give live birth, and nurse their young; they j | yes |

## run-2

Tool calls: {'ground': 3, 'send': 3, 'pin': 2}. `ground` verdicts: {'CORRECTED': 2, 'REFUTES': 1}.

| Question | Answer given | Correct |
|---|---|---|
| I'm about to send a payment in DOVU, the ERC-20 token at 0x2aeAbde1aB7… | DOVU (0x2aeAbde1aB736c59E9A19BeD67681869eEF39526) uses **8 decimals** (confirmed on-chain via decimals()).\n\nTo pay, e.g., 100 DOVU: raw amount = 100 × 10^8 =  | yes |
| Same question for Schuman EUR P (EUROP) at 0x888883b5F5D21fb10Dfeb70e8… | Schuman EUR P (EUROP) at 0x888883b5F5D21fb10Dfeb70e8f9722B9FB0E5E51 uses **6 decimals** (confirmed on-chain via decimals()).\n\nE.g., 100 EUROP: raw amount = 10 | yes |
| Different topic: are whales fish?… | No — whales are not fish. They are mammals (they breathe air, are warm-blooded, nurse their young, and descended from land-dwelling ancestors). The grounding ch | yes |

## run-3

Tool calls: {'ground': 3, 'pin': 2, 'send': 3, 'nal': 1}. `ground` verdicts: {'CORRECTED': 2, 'SUPPORTS': 1}.

| Question | Answer given | Correct |
|---|---|---|
| I'm about to send a payment in DOVU, the ERC-20 token at 0x2aeAbde1aB7… | DOVU (0x2aeAbde1aB736c59E9A19BeD67681869eEF39526) uses **8 decimals**. So a payment of 1,000 DOVU = 100000000000000 raw units (amount × 10^8). You're set to sen | yes |
| Same question for Schuman EUR P (EUROP) at 0x888883b5F5D21fb10Dfeb70e8… | EUROP (0x888883b5F5D21fb10Dfeb70e8f9722B9FB0E5E51) uses **6 decimals**. So 1,000 EUROP = 1,000,000,000 raw units (amount × 10^6) — note this differs from DOVU's | yes |
| Different topic: are whales fish?… | No — whales are **not fish**. They're mammals: they breathe air, are warm-blooded, give live birth, and nurse their young. Falsum-inference on (mammal → fish) c | yes |

## Notes (read from the logs, not scored)

- **The agent decided to use `ground` on its own.** The user messages never ask for verification. Every token question was grounded, and each came back CORRECTED from the chain (8 and 6 decimals), where ASI:One by itself answers 18 (see `notes` in the script).
- **The UNKNOWN hint works.** In run-1 the first premise, `decimals-18`, was in a shape no source checks. The UNKNOWN reply lists the shapes that are checkable, and the agent's next call, `(× 0x2aeA… 18) decimals`, was CORRECTED to 8.
- **Grounding fixes facts, not arithmetic.** Run-3 says "1,000 DOVU = 100000000000000 raw units", but with 8 decimals that is 100,000,000,000. The grounded fact was right; the model's multiplication on top of it was not.
- **NAL inference ran through the restricted `nal` skill** (run-3: whale → mammal, mammal → fish with f = 0).
- **These sessions follow two fixes found in earlier sessions with the same script:**
  - `ground` used to return 16–64 copies of its answer under full Omega. This was the duplicate-import bug in `docs/UPSTREAM_BUGS.md`, now worked around in the plugin.
  - One session never answered the token questions. The agent kept writing `(--> X (decimals N))`, a shape the source then rejected; it is now accepted, and UNKNOWN lists the checkable shapes.
