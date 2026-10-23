# Grounding benchmark

Items: 84 (onchain_longtail), chains: 0. Sources: record (sources.json).

### LLM: asione:asi1 (ASI:One, temperature 0)

1 run(s). Mean ± sd across runs.

| Metric | Better | baseline | discount | grounded |
|---|---|---|---|---|
| False premises reaching ACT | lower | 0.964 | 0.643 | n/a |
| True premises reaching ACT | higher | 0.964 | 0.855 | 1.000 |
| Precision of ACT premises | higher | 0.662 | 0.723 | 1.000 |
| Belief accuracy (f >= 0.5 matches truth) | higher | 0.663 | 0.663 | 1.000 |
| Brier score of NAL expectation | lower | 0.263 | 0.234 | 0.002 |
| Swapped relations still acted on | lower | n/a | n/a | n/a |
| False multi-hop conclusions reaching ACT | lower | n/a | n/a | n/a |
| True multi-hop conclusions reaching ACT | higher | n/a | n/a | n/a |
| Mean confidence of true conclusions | higher | n/a | n/a | n/a |

Grounded verdicts (all runs): CORRECTED 28, SUPPORTS 55, UNKNOWN 1

### Premise formulation by the LLM

| Outcome | Count | Share |
|---|---|---|
| Canonical statement | 52 | 61.9% |
| Equivalent phrasing (e.g. smart_contract) | 3 | 3.6% |
| Relation swapped | 0 | 0.0% |
| Well-formed answer with the wrong value | 28 | 33.3% |
| Other form (granularity, copula, naming) | 1 | 1.2% |
| Unparseable output | 0 | 0.0% |
| Refused | 0 | 0.0% |

Factual belief correct on 55 of 83 gradable premises (66.3%).

### Source coverage on canonical statements

Agrees 84, disagrees 0, unknown 0.

| Item | Statement | Gold | Verdict | Source agrees |
|---|---|---|---|---|
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
