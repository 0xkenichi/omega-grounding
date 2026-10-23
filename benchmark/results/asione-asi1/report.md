# Grounding benchmark

Items: 151 (taxonomy, onchain, onchain_longtail), chains: 12. Sources: record (sources.json).

### LLM: asione:asi1 (ASI:One, temperature 0)

1 run(s). Mean ± sd across runs.

| Metric | Better | baseline | discount | grounded |
|---|---|---|---|---|
| False premises reaching ACT | lower | 0.538 | 0.365 | 0.000 |
| True premises reaching ACT | higher | 0.958 | 0.896 | 0.992 |
| Precision of ACT premises | higher | 0.767 | 0.819 | 1.000 |
| Belief accuracy (f >= 0.5 matches truth) | higher | 0.797 | 0.797 | 0.993 |
| Brier score of NAL expectation | lower | 0.163 | 0.148 | 0.013 |
| Swapped relations still acted on | lower | n/a | n/a | n/a |
| False multi-hop conclusions reaching ACT | lower | 0.000 | 0.000 | 0.000 |
| True multi-hop conclusions reaching ACT | higher | 1.000 | 1.000 | 0.875 |
| Mean confidence of true conclusions | higher | 0.961 | 0.677 | 0.700 |

Grounded verdicts (all runs): CORRECTED 28, REFUTES 30, SUPPORTS 91, UNKNOWN 1

### Premise formulation by the LLM

| Outcome | Count | Share |
|---|---|---|
| Canonical statement | 113 | 74.8% |
| Equivalent phrasing (e.g. smart_contract) | 7 | 4.6% |
| Relation swapped | 0 | 0.0% |
| Well-formed answer with the wrong value | 28 | 18.5% |
| Other form (granularity, copula, naming) | 2 | 1.3% |
| Unparseable output | 0 | 0.0% |
| Refused | 0 | 0.0% |

Factual belief correct on 118 of 148 gradable premises (79.7%).

### Source coverage on canonical statements

Agrees 145, disagrees 6, unknown 0.

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
| L01 | `(--> (× ach 8) decimals)` | True | SUPPORTS | yes |
| L02 | `(--> (× acu 12) decimals)` | True | SUPPORTS | yes |
| L03 | `(--> (× alice 6) decimals)` | True | SUPPORTS | yes |
| L04 | `(--> (× ast 4) decimals)` | True | SUPPORTS | yes |
| L05 | `(--> (× audd 6) decimals)` | True | SUPPORTS | yes |
| L06 | `(--> (× ausd 6) decimals)` | True | SUPPORTS | yes |
| L07 | `(--> (× axl 6) decimals)` | True | SUPPORTS | yes |
| L08 | `(--> (× bdx 9) decimals)` | True | SUPPORTS | yes |
| L09 | `(--> (× bitcoin 8) decimals)` | True | SUPPORTS | yes |
| L10 | `(--> (× cbbtc 8) decimals)` | True | SUPPORTS | yes |
| L11 | `(--> (× chr 6) decimals)` | True | SUPPORTS | yes |
| L12 | `(--> (× coval 8) decimals)` | True | SUPPORTS | yes |
| L13 | `(--> (× cro 8) decimals)` | True | SUPPORTS | yes |
| L14 | `(--> (× cube 8) decimals)` | True | SUPPORTS | yes |
| L15 | `(--> (× cvc 8) decimals)` | True | SUPPORTS | yes |
| L16 | `(--> (× dar 6) decimals)` | True | SUPPORTS | yes |
| L17 | `(--> (× dent 8) decimals)` | True | SUPPORTS | yes |
| L18 | `(--> (× dovu 8) decimals)` | True | SUPPORTS | yes |
| L19 | `(--> (× elizaos 9) decimals)` | True | SUPPORTS | yes |
| L20 | `(--> (× es 6) decimals)` | True | SUPPORTS | yes |
| L21 | `(--> (× eurc 6) decimals)` | True | SUPPORTS | yes |
| L22 | `(--> (× europ 6) decimals)` | True | SUPPORTS | yes |
| L23 | `(--> (× eurq 6) decimals)` | True | SUPPORTS | yes |
| L24 | `(--> (× eurr 6) decimals)` | True | SUPPORTS | yes |
| L25 | `(--> (× floki 9) decimals)` | True | SUPPORTS | yes |
| L26 | `(--> (× folks 6) decimals)` | True | SUPPORTS | yes |
| L27 | `(--> (× frnt 6) decimals)` | True | SUPPORTS | yes |
| L28 | `(--> (× gala 8) decimals)` | True | SUPPORTS | yes |
| L29 | `(--> (× gusd 2) decimals)` | True | SUPPORTS | yes |
| L30 | `(--> (× gyen 6) decimals)` | True | SUPPORTS | yes |
| L31 | `(--> (× kbtc 8) decimals)` | True | SUPPORTS | yes |
| L32 | `(--> (× kuji 6) decimals)` | True | SUPPORTS | yes |
| L33 | `(--> (× move 8) decimals)` | True | SUPPORTS | yes |
| L34 | `(--> (× mtl 8) decimals)` | True | SUPPORTS | yes |
| L35 | `(--> (× mxnb 6) decimals)` | True | SUPPORTS | yes |
| L36 | `(--> (× neiro 9) decimals)` | True | SUPPORTS | yes |
| L37 | `(--> (× orn 8) decimals)` | True | SUPPORTS | yes |
| L38 | `(--> (× ousd 6) decimals)` | True | SUPPORTS | yes |
| L39 | `(--> (× powr 6) decimals)` | True | SUPPORTS | yes |
| L40 | `(--> (× pro 8) decimals)` | True | SUPPORTS | yes |
| L41 | `(--> (× pyusd 6) decimals)` | True | SUPPORTS | yes |
| L42 | `(--> (× qcad 6) decimals)` | True | SUPPORTS | yes |
| L43 | `(--> (× qrdo 8) decimals)` | True | SUPPORTS | yes |
| L44 | `(--> (× rlc 9) decimals)` | True | SUPPORTS | yes |
| L45 | `(--> (× shx 7) decimals)` | True | SUPPORTS | yes |
| L46 | `(--> (× slay 6) decimals)` | True | SUPPORTS | yes |
| L47 | `(--> (× slp 0) decimals)` | True | SUPPORTS | yes |
| L48 | `(--> (× sofid 6) decimals)` | True | SUPPORTS | yes |
| L49 | `(--> (× sol 9) decimals)` | True | SUPPORTS | yes |
| L50 | `(--> (× spx 8) decimals)` | True | SUPPORTS | yes |
| L51 | `(--> (× storj 8) decimals)` | True | SUPPORTS | yes |
| L52 | `(--> (× swftc 8) decimals)` | True | SUPPORTS | yes |
| L53 | `(--> (× tel 2) decimals)` | True | SUPPORTS | yes |
| L54 | `(--> (× time 8) decimals)` | True | SUPPORTS | yes |
| L55 | `(--> (× tlm 4) decimals)` | True | SUPPORTS | yes |
| L56 | `(--> (× token 9) decimals)` | True | SUPPORTS | yes |
| L57 | `(--> (× tru 8) decimals)` | True | SUPPORTS | yes |
| L58 | `(--> (× usat 6) decimals)` | True | SUPPORTS | yes |
| L59 | `(--> (× usdg 6) decimals)` | True | SUPPORTS | yes |
| L60 | `(--> (× usdq 6) decimals)` | True | SUPPORTS | yes |
| L61 | `(--> (× usdr 6) decimals)` | True | SUPPORTS | yes |
| L62 | `(--> (× verona 6) decimals)` | True | SUPPORTS | yes |
| L63 | `(--> (× vgx 8) decimals)` | True | SUPPORTS | yes |
| L64 | `(--> (× wanlog 12) decimals)` | True | SUPPORTS | yes |
| L65 | `(--> (× wbt 8) decimals)` | True | SUPPORTS | yes |
| L66 | `(--> (× wbtc 8) decimals)` | True | SUPPORTS | yes |
| L67 | `(--> (× wfb 8) decimals)` | True | SUPPORTS | yes |
| L68 | `(--> (× xaut 6) decimals)` | True | SUPPORTS | yes |
| L69 | `(--> (× xsgd 6) decimals)` | True | SUPPORTS | yes |
| L70 | `(--> (× lpt 18) decimals)` | True | SUPPORTS | yes |
| L71 | `(--> (× yb 18) decimals)` | True | SUPPORTS | yes |
| L72 | `(--> (× mezo 18) decimals)` | True | SUPPORTS | yes |
| L73 | `(--> (× almanak 18) decimals)` | True | SUPPORTS | yes |
| L74 | `(--> (× ev 18) decimals)` | True | SUPPORTS | yes |
| L75 | `(--> (× planck 18) decimals)` | True | SUPPORTS | yes |
| L76 | `(--> (× omni 18) decimals)` | True | SUPPORTS | yes |
| L77 | `(--> (× matic 18) decimals)` | True | SUPPORTS | yes |
| L78 | `(--> (× zrx 18) decimals)` | True | SUPPORTS | yes |
| L79 | `(--> (× gno 18) decimals)` | True | SUPPORTS | yes |
| L80 | `(--> (× ogn 18) decimals)` | True | SUPPORTS | yes |
| L81 | `(--> (× kernel 18) decimals)` | True | SUPPORTS | yes |
| L82 | `(--> (× rgt 18) decimals)` | True | SUPPORTS | yes |
| L83 | `(--> (× drep 18) decimals)` | True | SUPPORTS | yes |
| L84 | `(--> (× pepecoin 18) decimals)` | True | SUPPORTS | yes |
