"""Where benchmark premises come from.

SyntheticLLM is a seeded noise model whose default rates are the ones Omega's
docs/reference-failure-modes.md reports for its LLM premise step. It is a
stress model, not a claim about any particular LLM; use ClaudeAtomizer to
measure a real model on the same items.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from typing import Optional, Tuple

from ..nal import ParseError, Term, Truth, parse, reverse
from .datasets import Item

Premise = Tuple[Term, Truth]


@dataclass(frozen=True)
class NoiseModel:
    factual_error_rate: float  # chance the LLM believes the wrong truth value
    swap_rate: float           # chance it writes (--> B A) for (--> A B)
    confidence_low: float = 0.70
    confidence_high: float = 0.95


PROFILES = {
    # Omega's measured rates: ~55% factual accuracy, up to 16.6% swaps,
    # confidence ~15 points too high (stated 0.70 averaging ~0.55 actual).
    "omega-docs": NoiseModel(factual_error_rate=0.45, swap_rate=0.166),
    # A strong model on easy facts.
    "mild": NoiseModel(factual_error_rate=0.10, swap_rate=0.05),
}


class SyntheticLLM:
    def __init__(self, noise: NoiseModel, seed: int):
        self.noise = noise
        self.rng = random.Random(seed)
        self.name = "synthetic"

    def premise(self, item: Item) -> Optional[Premise]:
        believes = item.gold if self.rng.random() >= self.noise.factual_error_rate else not item.gold
        statement = item.statement
        if item.swappable and self.rng.random() < self.noise.swap_rate:
            statement = reverse(statement)
        confidence = self.rng.uniform(self.noise.confidence_low, self.noise.confidence_high)
        return statement, Truth(1.0 if believes else 0.0, round(confidence, 4))


SYSTEM_PROMPT = """You convert one English sentence into a single Non-Axiomatic Logic premise for the Omega agent's MeTTa reasoner.

Conventions:
- Inheritance: (--> subject predicate), e.g. "Dolphins are mammals" -> (--> dolphin mammal).
- Use lowercase singular atoms; join multi-word terms with underscores: string_instrument.
- Properties: (--> subject ([] property)), e.g. "X is upgradeable" -> (--> x ([] upgradeable)).
- Relations with a value: (--> (× subject value) relation), e.g. "USDC has 6 decimals" -> (--> (× usdc 6) decimals).
- Name tokens by their lowercase ticker (usdc, weth, dai, steth, aave_v3_pool) or by 0x address.

frequency is 1.0 if you believe the sentence is true and 0.0 if you believe it is false.
confidence (0 to 1) is how sure you are, as you would set it in an (stv frequency confidence) truth value."""

SCHEMA = {
    "type": "object",
    "properties": {
        "statement": {"type": "string", "description": "The MeTTa statement, without a truth value."},
        "frequency": {"type": "number"},
        "confidence": {"type": "number"},
    },
    "required": ["statement", "frequency", "confidence"],
    "additionalProperties": False,
}


class ClaudeAtomizer:
    """Asks Claude to atomize each item's sentence. Costs API tokens per item."""

    def __init__(self, model: str = "claude-opus-5-5", effort: str = "medium"):
        import anthropic  # optional dependency: pip install 'omega-grounding[claude]'

        self.client = anthropic.Anthropic()
        self.model = model
        self.effort = effort
        self.name = f"claude:{model}"
        self.refusals = 0
        self.unparseable = 0

    def premise(self, item: Item) -> Optional[Premise]:
        response = self.client.beta.messages.create(
            model=self.model,
            max_tokens=16000,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            output_config={"effort": self.effort, "format": {"type": "json_schema", "schema": SCHEMA}},
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": item.text}],
        )
        if response.stop_reason == "refusal":
            self.refusals += 1
            return None
        text = next((b.text for b in response.content if b.type == "text"), "")
        try:
            data = json.loads(text)
            statement = parse(data["statement"])
        except (ValueError, KeyError, ParseError):
            self.unparseable += 1
            return None
        f = min(1.0, max(0.0, float(data["frequency"])))
        c = min(0.99, max(0.0, float(data["confidence"])))
        return statement, Truth(f, c)
