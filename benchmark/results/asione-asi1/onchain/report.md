# Grounding benchmark

Items: 24 (onchain), chains: 0. Sources: record (sources.json).

### LLM: asione:asi1 (ASI:One, temperature 0)

1 run(s). Mean ± sd across runs.

| Metric | Better | baseline | discount | grounded |
|---|---|---|---|---|
| False premises reaching ACT | lower | 0.091 | 0.091 | 0.000 |
| True premises reaching ACT | higher | 0.846 | 0.846 | 0.923 |
| Precision of ACT premises | higher | 0.917 | 0.917 | 1.000 |
| Belief accuracy (f >= 0.5 matches truth) | higher | 0.917 | 0.917 | 0.958 |
| Brier score of NAL expectation | lower | 0.085 | 0.082 | 0.044 |
| Swapped relations still acted on | lower | n/a | n/a | n/a |
| False multi-hop conclusions reaching ACT | lower | n/a | n/a | n/a |
| True multi-hop conclusions reaching ACT | higher | n/a | n/a | n/a |
| Mean confidence of true conclusions | higher | n/a | n/a | n/a |

Grounded verdicts (all runs): REFUTES 12, SUPPORTS 12

### Premise formulation by the LLM

| Outcome | Count | Share |
|---|---|---|
| Canonical statement | 20 | 83.3% |
| Equivalent phrasing (e.g. smart_contract) | 4 | 16.7% |
| Relation swapped | 0 | 0.0% |
| Well-formed answer with the wrong value | 0 | 0.0% |
| Other form (granularity, copula, naming) | 0 | 0.0% |
| Unparseable output | 0 | 0.0% |
| Refused | 0 | 0.0% |

Factual belief correct on 22 of 24 gradable premises (91.7%).

### Source coverage on canonical statements

Agrees 23, disagrees 1, unknown 0.

| Item | Statement | Gold | Verdict | Source agrees |
|---|---|---|---|---|
| o01 | `(--> usdc ([] contract))` | True | SUPPORTS | yes |
| o02 | `(--> 0xd8da6bf26964af9d7eed9e03e53415d37aa96045 ([] contract))` | False | REFUTES | yes |
| o03 | `(--> usdc ([] upgradeable))` | True | SUPPORTS | yes |
| o04 | `(--> weth ([] upgradeable))` | False | REFUTES | yes |
| o05 | `(--> dai ([] upgradeable))` | False | REFUTES | yes |
| o06 | `(--> usdt ([] upgradeable))` | False | REFUTES | yes |
| o07 | `(--> steth ([] upgradeable))` | True | REFUTES | **no** |
| o08 | `(--> aave_v3_pool ([] upgradeable))` | True | SUPPORTS | yes |
| o09 | `(--> uni ([] upgradeable))` | False | REFUTES | yes |
| o10 | `(--> link ([] upgradeable))` | False | REFUTES | yes |
| o11 | `(--> (× usdc 6) decimals)` | True | SUPPORTS | yes |
| o12 | `(--> (× usdc 18) decimals)` | False | REFUTES | yes |
| o13 | `(--> (× usdt 6) decimals)` | True | SUPPORTS | yes |
| o14 | `(--> (× usdt 18) decimals)` | False | REFUTES | yes |
| o15 | `(--> (× dai 18) decimals)` | True | SUPPORTS | yes |
| o16 | `(--> (× dai 6) decimals)` | False | REFUTES | yes |
| o17 | `(--> (× weth 18) decimals)` | True | SUPPORTS | yes |
| o18 | `(--> (× link 18) decimals)` | True | SUPPORTS | yes |
| o19 | `(--> (× uni 18) decimals)` | True | SUPPORTS | yes |
| o20 | `(--> (× weth WETH) symbol)` | True | SUPPORTS | yes |
| o21 | `(--> (× link LINK) symbol)` | True | SUPPORTS | yes |
| o22 | `(--> (× uni UNISWAP) symbol)` | False | REFUTES | yes |
| o23 | `(--> (× dai DAI) symbol)` | True | SUPPORTS | yes |
| o24 | `(--> (× usdt USDC) symbol)` | False | REFUTES | yes |
