# Grounding benchmark

Items: 67 (taxonomy, onchain), chains: 12. Sources: replay (sources.json).

### Synthetic LLM, profile `omega-docs` (factual error 0.45, swap 0.166)

30 run(s). Mean ± sd across runs.

| Metric | Better | baseline | discount | grounded |
|---|---|---|---|---|
| False premises reaching ACT | lower | 0.475 ± 0.094 | 0.475 ± 0.094 | 0.025 ± 0.030 |
| True premises reaching ACT | higher | 0.563 ± 0.076 | 0.563 ± 0.076 | 0.718 ± 0.054 |
| Precision of ACT premises | higher | 0.595 ± 0.069 | 0.595 ± 0.069 | 0.980 ± 0.024 |
| Belief accuracy (f >= 0.5 matches truth) | higher | 0.546 ± 0.065 | 0.546 ± 0.065 | 0.846 ± 0.025 |
| Brier score of NAL expectation | lower | 0.383 ± 0.053 | 0.333 ± 0.043 | 0.109 ± 0.014 |
| Swapped relations still acted on | lower | 0.516 ± 0.208 | 0.516 ± 0.208 | 0.026 ± 0.056 |
| False multi-hop conclusions reaching ACT | lower | 0.075 ± 0.134 | 0.008 ± 0.046 | 0.000 ± 0.000 |
| True multi-hop conclusions reaching ACT | higher | 0.200 ± 0.142 | 0.058 ± 0.091 | 0.237 ± 0.159 |
| Mean confidence of true conclusions | higher | 0.224 ± 0.157 | 0.151 ± 0.106 | 0.371 ± 0.080 |

Grounded verdicts (all runs): CORRECTED 138, REFUTES 914, SUPPORTS 958

### Synthetic LLM, profile `mild` (factual error 0.1, swap 0.05)

30 run(s). Mean ± sd across runs.

| Metric | Better | baseline | discount | grounded |
|---|---|---|---|---|
| False premises reaching ACT | lower | 0.137 ± 0.070 | 0.137 ± 0.070 | 0.003 ± 0.010 |
| True premises reaching ACT | higher | 0.899 ± 0.045 | 0.899 ± 0.045 | 0.828 ± 0.036 |
| Precision of ACT premises | higher | 0.910 ± 0.047 | 0.910 ± 0.047 | 0.998 ± 0.008 |
| Belief accuracy (f >= 0.5 matches truth) | higher | 0.884 ± 0.033 | 0.884 ± 0.033 | 0.915 ± 0.021 |
| Brier score of NAL expectation | lower | 0.105 ± 0.027 | 0.106 ± 0.022 | 0.051 ± 0.008 |
| Swapped relations still acted on | lower | 0.565 ± 0.364 | 0.565 ± 0.364 | 0.013 ± 0.065 |
| False multi-hop conclusions reaching ACT | lower | 0.050 ± 0.102 | 0.008 ± 0.046 | 0.000 ± 0.000 |
| True multi-hop conclusions reaching ACT | higher | 0.713 ± 0.151 | 0.146 ± 0.109 | 0.621 ± 0.111 |
| Mean confidence of true conclusions | higher | 0.535 ± 0.079 | 0.352 ± 0.052 | 0.519 ± 0.032 |

Grounded verdicts (all runs): CORRECTED 43, REFUTES 919, SUPPORTS 1048

### Source coverage on canonical statements

Agrees 61, disagrees 6, unknown 0.

| Item | Statement | Gold | Verdict | Source agrees |
|---|---|---|---|---|
| t01 | `(--> dolphin mammal)` | True | SUPPORTS | yes |
| t02 | `(--> whale mammal)` | True | SUPPORTS | yes |
| t03 | `(--> bat mammal)` | True | SUPPORTS | yes |
| t04 | `(--> penguin bird)` | True | SUPPORTS | yes |
| t05 | `(--> ostrich bird)` | True | SUPPORTS | yes |
| t06 | `(--> shark fish)` | True | SUPPORTS | yes |
| t07 | `(--> salmon fish)` | True | SUPPORTS | yes |
| t08 | `(--> frog amphibian)` | True | SUPPORTS | yes |
| t09 | `(--> snake reptile)` | True | SUPPORTS | yes |
| t10 | `(--> spider arachnid)` | True | SUPPORTS | yes |
| t11 | `(--> mammal animal)` | True | SUPPORTS | yes |
| t12 | `(--> bird animal)` | True | SUPPORTS | yes |
| t13 | `(--> reptile animal)` | True | REFUTES | **no** |
| t14 | `(--> mammal synapsid)` | True | SUPPORTS | yes |
| t15 | `(--> insect hexapod)` | True | REFUTES | **no** |
| t16 | `(--> bird dinosaur)` | True | SUPPORTS | yes |
| t17 | `(--> dinosaur reptile)` | True | REFUTES | **no** |
| t18 | `(--> cat mammal)` | True | SUPPORTS | yes |
| t19 | `(--> dog mammal)` | True | SUPPORTS | yes |
| t20 | `(--> oak tree)` | True | REFUTES | **no** |
| t21 | `(--> earth planet)` | True | SUPPORTS | yes |
| t22 | `(--> mars planet)` | True | SUPPORTS | yes |
| t23 | `(--> sun star)` | True | SUPPORTS | yes |
| t24 | `(--> violin string_instrument)` | True | SUPPORTS | yes |
| t25 | `(--> guitar string_instrument)` | True | SUPPORTS | yes |
| t26 | `(--> string_instrument musical_instrument)` | True | SUPPORTS | yes |
| t27 | `(--> planet astronomical_object)` | True | SUPPORTS | yes |
| t28 | `(--> iron metal)` | True | REFUTES | **no** |
| t29 | `(--> gold metal)` | True | SUPPORTS | yes |
| f01 | `(--> whale fish)` | False | REFUTES | yes |
| f02 | `(--> bat bird)` | False | REFUTES | yes |
| f03 | `(--> penguin mammal)` | False | REFUTES | yes |
| f04 | `(--> spider insect)` | False | REFUTES | yes |
| f05 | `(--> dolphin fish)` | False | REFUTES | yes |
| f06 | `(--> snake amphibian)` | False | REFUTES | yes |
| f07 | `(--> shark mammal)` | False | REFUTES | yes |
| f08 | `(--> sun planet)` | False | REFUTES | yes |
| f09 | `(--> moon planet)` | False | REFUTES | yes |
| f10 | `(--> violin keyboard_instrument)` | False | REFUTES | yes |
| f11 | `(--> frog reptile)` | False | REFUTES | yes |
| f12 | `(--> octopus fish)` | False | REFUTES | yes |
| f13 | `(--> mars star)` | False | REFUTES | yes |
| f14 | `(--> iron noble_gas)` | False | REFUTES | yes |
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
