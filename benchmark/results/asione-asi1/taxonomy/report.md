# Grounding benchmark

Items: 43 (taxonomy), chains: 12. Sources: record (sources.json).

### LLM: asione:asi1 (ASI:One, temperature 0)

1 run(s). Mean ± sd across runs.

| Metric | Better | baseline | discount | grounded |
|---|---|---|---|---|
| False premises reaching ACT | lower | 0.000 | 0.000 | 0.000 |
| True premises reaching ACT | higher | 1.000 | 1.000 | 1.000 |
| Precision of ACT premises | higher | 1.000 | 1.000 | 1.000 |
| Belief accuracy (f >= 0.5 matches truth) | higher | 1.000 | 1.000 | 1.000 |
| Brier score of NAL expectation | lower | 0.006 | 0.013 | 0.016 |
| Swapped relations still acted on | lower | n/a | n/a | n/a |
| False multi-hop conclusions reaching ACT | lower | 0.000 | 0.000 | 0.000 |
| True multi-hop conclusions reaching ACT | higher | 1.000 | 1.000 | 0.875 |
| Mean confidence of true conclusions | higher | 0.961 | 0.677 | 0.700 |

Grounded verdicts (all runs): REFUTES 18, SUPPORTS 24

### Premise formulation by the LLM

| Outcome | Count | Share |
|---|---|---|
| Canonical statement | 41 | 95.3% |
| Equivalent phrasing (e.g. smart_contract) | 0 | 0.0% |
| Relation swapped | 0 | 0.0% |
| Well-formed answer with the wrong value | 0 | 0.0% |
| Other form (granularity, copula, naming) | 1 | 2.3% |
| Unparseable output | 0 | 0.0% |
| Refused | 0 | 0.0% |

Factual belief correct on 41 of 41 gradable premises (100.0%).

### Source coverage on canonical statements

Agrees 38, disagrees 5, unknown 0.

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
