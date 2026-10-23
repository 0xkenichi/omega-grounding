"""Automated premise grounding for Omega.

Omega's LLM turns language into NAL premises; its own failure-mode report
measures that step as the main source of error. This package checks each
premise against an external source, corrects relation swaps and wrong values,
and replaces the LLM's self-assigned confidence with one calibrated to source
quality, using the same NAL truth functions Omega uses.
"""

__version__ = "0.1.0"
