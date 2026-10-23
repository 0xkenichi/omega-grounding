from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from .evidence import DEFAULT_LLM_DISCOUNT, Evidence, GroundedPremise, Verdict, combine
from .nal import Term, Truth, fmt
from .sources import EvmSource, Source, WikidataSource
from .sources.evm import DEFAULT_RPC_URL
from .transport import CassetteTransport, HttpTransport


# Returned with UNKNOWN so an agent can rephrase in one step instead of guessing.
SUPPORTED_SHAPES = ("Checkable shapes: (--> a b) between plain terms, e.g. (--> dolphin mammal); "
                    "on-chain, with TOKEN a ticker or 0x address: (--> (× TOKEN N) decimals), "
                    "(--> (× TOKEN SYMBOL) symbol), (--> TOKEN ([] contract)), (--> TOKEN ([] upgradeable)). "
                    "To look up a value, pass any N: a wrong value comes back CORRECTED.")


class Grounder:
    """Routes a statement to the first source that can decide it."""

    def __init__(self, sources: Sequence[Source], llm_discount: float = DEFAULT_LLM_DISCOUNT,
                 transport=None):
        self.sources: List[Source] = list(sources)
        self.llm_discount = llm_discount
        self.transport = transport
        self._cache: Dict[str, Evidence] = {}

    def close(self) -> None:
        """Flush a recording cassette, if any."""
        if hasattr(self.transport, "save"):
            self.transport.save()

    def evidence(self, statement: Term) -> Evidence:
        key = fmt(statement)
        if key not in self._cache:
            self._cache[key] = self._lookup(statement)
        return self._cache[key]

    def _lookup(self, statement: Term) -> Evidence:
        result = Evidence.unknown("no source covers this statement. " + SUPPORTED_SHAPES)
        for source in self.sources:
            if source.supports(statement):
                result = source.check(statement)
                if result.verdict is not Verdict.UNKNOWN:
                    return result
        return result

    def ground(self, statement: Term, llm_truth: Truth) -> GroundedPremise:
        return combine(statement, llm_truth, self.evidence(statement), self.llm_discount)


def default_grounder(cassette: Optional[Path] = None, mode: str = "live",
                     rpc_url: Optional[str] = None, closed_world: bool = True) -> Grounder:
    """Wikidata + Ethereum mainnet. mode: live | record | replay (needs cassette)."""
    http = HttpTransport(min_interval=0.3)
    transport = http if mode == "live" else CassetteTransport(cassette, mode, http)
    rpc = rpc_url or os.environ.get("OMEGA_GROUNDING_RPC_URL", DEFAULT_RPC_URL)
    return Grounder([
        EvmSource(transport, rpc_url=rpc),
        WikidataSource(transport, closed_world=closed_world),
    ], transport=transport)
