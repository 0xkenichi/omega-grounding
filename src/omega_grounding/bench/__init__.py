"""Benchmark: does grounding reduce the failure modes Omega documents?

Three pipelines see the same LLM premises:
    baseline   premises as the LLM wrote them
    discount   Omega's manual mitigation: subtract 15 points of confidence
    grounded   this package: source lookup, correction, revision
and are scored on premise-level and chain-level (multi-hop deduction) metrics.
"""
