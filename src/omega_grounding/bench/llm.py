"""Where benchmark premises come from.

SyntheticLLM is a seeded noise model whose default rates are the ones Omega's
docs/reference-failure-modes.md reports for its LLM premise step. It is a
stress model, not a claim about any particular LLM; use ClaudeAtomizer or
OllamaAtomizer to measure a real model on the same items.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Optional, Tuple

from ..nal import ParseError, Term, Truth, fmt, parse, reverse
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


SYSTEM_PROMPT = """You convert one English sentence into a single Non-Axiomatic Logic premise for the Omega agent's MeTTa reasoner. If the sentence is a question, answer it from your own knowledge and write the answer as the premise.

Conventions:
- Inheritance: (--> subject predicate), e.g. "Dolphins are mammals" -> (--> dolphin mammal).
- Use lowercase singular atoms; join multi-word terms with underscores: string_instrument.
- Properties: (--> subject ([] property)), e.g. "X is upgradeable" -> (--> x ([] upgradeable)).
- Relations with a value: (--> (× subject value) relation), e.g. "USDC has 6 decimals" -> (--> (× usdc 6) decimals).
- Name tokens by their lowercase ticker (usdc, weth, dai, steth, aave_v3_pool) or by 0x address.

frequency is 1.0 if you believe the sentence (or your answer) is true and 0.0 if you believe it is false.
confidence (0 to 1) is how sure you are, as you would set it in an (stv frequency confidence) truth value."""

PROMPT_ID = hashlib.sha256(SYSTEM_PROMPT.encode("utf-8")).hexdigest()[:12]

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


def _premise_from_json(text: str) -> Optional[Premise]:
    # Models without schema-constrained output may wrap the JSON in prose or fences.
    match = re.search(r"\{.*\}", text, re.DOTALL)
    try:
        data = json.loads(match.group(0) if match else text)
        statement = parse(data["statement"])
        f = min(1.0, max(0.0, float(data["frequency"])))
        c = min(0.99, max(0.0, float(data["confidence"])))
    except (ValueError, KeyError, TypeError, ParseError):
        return None
    return statement, Truth(f, c)


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
        premise = _premise_from_json(next((b.text for b in response.content if b.type == "text"), ""))
        if premise is None:
            self.unparseable += 1
        return premise


class OllamaAtomizer:
    """Asks a local open-weights model served by Ollama. No API key, no cost."""

    def __init__(self, model: str = "qwen2.5:7b", url: str = "http://127.0.0.1:11434", timeout: float = 600.0):
        self.model = model
        self.url = url.rstrip("/")
        self.timeout = timeout
        self.name = f"ollama:{model}"
        self.refusals = 0
        self.unparseable = 0

    def premise(self, item: Item) -> Optional[Premise]:
        body = json.dumps({
            "model": self.model,
            "stream": False,
            "format": SCHEMA,  # Ollama structured outputs: constrain to the JSON schema
            "options": {"temperature": 0},
            "messages": [{"role": "system", "content": SYSTEM_PROMPT},
                         {"role": "user", "content": item.text}],
        }).encode("utf-8")
        req = urllib.request.Request(f"{self.url}/api/chat", data=body,
                                     headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            reply = json.loads(resp.read().decode("utf-8"))
        premise = _premise_from_json(reply.get("message", {}).get("content", ""))
        if premise is None:
            self.unparseable += 1
        return premise


class OpenAICompatAtomizer:
    """Any OpenAI-compatible chat endpoint; ASI:One by default (as Omega's ASIOne provider)."""

    def __init__(self, model: str = "asi1", url: str = "https://api.asi1.ai/v1",
                 key_env: str = "ASIONE_API_KEY", label: str = "asione", timeout: float = 300.0):
        self.key = os.environ.get(key_env, "").strip()
        if not self.key:
            raise SystemExit(f"{key_env} is not set")
        self.model = model
        self.url = url.rstrip("/")
        self.timeout = timeout
        self.name = f"{label}:{model}"
        self.schema_supported = True
        self.refusals = 0
        self.unparseable = 0

    def _post(self, payload: dict, attempts: int = 6) -> dict:
        """POST with backoff on dropped connections, rate limits and server errors."""
        data = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.key}",
                   "User-Agent": "omega-grounding/0.1"}
        for attempt in range(attempts):
            req = urllib.request.Request(f"{self.url}/chat/completions", data=data, method="POST",
                                         headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                if exc.code not in (429, 500, 502, 503, 504) or attempt == attempts - 1:
                    raise
                wait = float(exc.headers.get("Retry-After") or 2 ** (attempt + 1))
            except (urllib.error.URLError, OSError):  # includes SSL errors and timeouts
                if attempt == attempts - 1:
                    raise
                wait = 2 ** (attempt + 1)
            time.sleep(min(wait, 120))
        raise RuntimeError("unreachable")

    def premise(self, item: Item) -> Optional[Premise]:
        payload = {
            "model": self.model,
            "temperature": 0,
            "messages": [{"role": "system", "content": SYSTEM_PROMPT + "\n\nReply with only a JSON object "
                          'with keys "statement", "frequency", "confidence".'},
                         {"role": "user", "content": item.text}],
        }
        if self.schema_supported:
            payload["response_format"] = {"type": "json_schema",
                                          "json_schema": {"name": "premise", "schema": SCHEMA, "strict": True}}
        try:
            reply = self._post(payload)
        except urllib.error.HTTPError as exc:
            if exc.code not in (400, 422) or not self.schema_supported:
                raise
            self.schema_supported = False  # endpoint rejects response_format: fall back to the prompt
            payload.pop("response_format")
            reply = self._post(payload)
        choice = (reply.get("choices") or [{}])[0]
        if choice.get("finish_reason") == "content_filter":
            self.refusals += 1
            return None
        premise = _premise_from_json(choice.get("message", {}).get("content") or "")
        if premise is None:
            self.unparseable += 1
        return premise


class CachedLLM:
    """Records each premise a real LLM wrote, so reruns reuse them and results are reproducible."""

    def __init__(self, llm, path):
        from pathlib import Path

        self.llm = llm
        self.path = Path(path)
        self.name = llm.name
        self._cache = {}
        if self.path.exists():
            for line in self.path.read_text().splitlines():
                row = json.loads(line)
                self._cache[row["id"]] = row

    @property
    def refusals(self):
        return self.llm.refusals

    @property
    def unparseable(self):
        return self.llm.unparseable

    def premise(self, item: Item) -> Optional[Premise]:
        row = self._cache.get(item.id)
        if (row is None or row.get("text") != item.text or row.get("model") != self.name
                or row.get("prompt") != PROMPT_ID):
            premise = self.llm.premise(item)
            row = {"id": item.id, "model": self.name, "prompt": PROMPT_ID, "text": item.text,
                   "statement": fmt(premise[0]) if premise else None,
                   "frequency": premise[1].f if premise else None,
                   "confidence": premise[1].c if premise else None}
            self._cache[item.id] = row
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a") as out:
                out.write(json.dumps(row, ensure_ascii=False) + "\n")
        if row["statement"] is None:
            return None
        return parse(row["statement"]), Truth(row["frequency"], row["confidence"])

    def save(self) -> None:
        """Rewrite the cache with one current row per item."""
        if self._cache:
            rows = sorted(self._cache.values(), key=lambda r: r["id"])
            self.path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
