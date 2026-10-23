"""Ethereum state as a primary source, read over plain JSON-RPC.

Supported statements (X is a 0x address or a name from the token registry):

    (--> X ([] contract))          X has contract code
    (--> X ([] upgradeable))       X is a proxy with a known implementation slot
    (--> (× X N) decimals)         ERC-20 decimals() == N
    (--> (× X S) symbol)           ERC-20 symbol() == S (case-insensitive)

A wrong decimals/symbol value is refuted and corrected to the on-chain value.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, Optional

from ..evidence import Evidence, SourceClass, Verdict
from ..nal import INHERITANCE, INT_SETS, PRODUCT, Term, Truth, is_statement
from ..transport import TransportError
from .base import Source

DEFAULT_RPC_URL = "https://ethereum-rpc.publicnode.com"
ADDRESS = re.compile(r"^0x[0-9a-fA-F]{40}$")

# Ethereum mainnet. Extend or replace via the `registry` argument.
CORE_TOKENS: Dict[str, str] = {
    "usdc": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
    "usdt": "0xdac17f958d2ee523a2206206994597c13d831ec7",
    "dai": "0x6b175474e89094c44da98b954eedeac495271d0f",
    "weth": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
    "link": "0x514910771af9ca656af840dff83e8264ecf986ca",
    "uni": "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984",
    "steth": "0xae7ab96520de3a18e5e111b5eaab095312d7fe84",
    "aave_v3_pool": "0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2",
}


def _bundled_tokens() -> Dict[str, str]:
    """~480 symbols from the Uniswap default token list (tools/build_token_registry.py)."""
    path = Path(__file__).with_name("tokens_mainnet.json")
    return json.loads(path.read_text())["tokens"] if path.exists() else {}


MAINNET_TOKENS: Dict[str, str] = {**_bundled_tokens(), **CORE_TOKENS}

PROXY_SLOTS = {
    # bytes32(uint256(keccak256('eip1967.proxy.implementation')) - 1)
    "EIP-1967 implementation": "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc",
    # bytes32(uint256(keccak256('eip1967.proxy.beacon')) - 1)
    "EIP-1967 beacon": "0xa3f0ad74e5423aebfd80d3ef4346578335a9a72aeaee59ff6cb3582b35133d50",
    # keccak256('org.zeppelinos.proxy.implementation'), used by early OpenZeppelin proxies (e.g. USDC)
    "OpenZeppelin legacy implementation": "0x7050c9e0f4ca769c69bd3a8ef740bc37934f8e2c036e5a723fd8ee048ed3f8c3",
}

SELECTOR_DECIMALS = "0x313ce567"
SELECTOR_SYMBOL = "0x95d89b41"
# EIP-7702: an EOA that delegated its code carries 0xef0100 || address.
DELEGATION_PREFIX = "0xef0100"

# How LLMs actually phrase these facts (Omega's "granularity mismatch"):
# (--> usdc smart_contract), (--> usdt upgradeable_proxy), (--> uni_token_contract ...).
PROPERTY_SYNONYMS = {
    "contract": "contract", "smart_contract": "contract", "contract_account": "contract",
    "upgradeable": "upgradeable", "upgradable": "upgradeable", "upgradeable_proxy": "upgradeable",
    "upgradable_proxy": "upgradeable", "proxy": "upgradeable", "proxy_contract": "upgradeable",
    "upgradeable_contract": "upgradeable", "upgradable_contract": "upgradeable",
}
RELATION_SYNONYMS = {
    "decimals": "decimals", "decimal_places": "decimals", "token_decimals": "decimals",
    "symbol": "symbol", "ticker": "symbol", "token_symbol": "symbol",
}
SUBJECT_SUFFIXES = ("_token_contract", "_contract", "_token")


def _canonical_subject(term: Term, registry: Dict[str, str]) -> Optional[str]:
    """A registry name for the token (also when given by address), else its address."""
    if not isinstance(term, str):
        return None
    if ADDRESS.match(term):
        address = term.lower()
        return next((name for name, a in registry.items() if a == address), address)
    name = term.lower()
    if name in registry:
        return name
    for suffix in SUBJECT_SUFFIXES:
        if name.endswith(suffix) and name[: -len(suffix)] in registry:
            return name[: -len(suffix)]
    return None


def canonical_form(statement: Term, registry: Optional[Dict[str, str]] = None) -> Optional[Term]:
    """Rewrite an on-chain statement into the one form the source checks, or None.

    (--> usdc smart_contract) and (--> usdc ([] contract)) both become
    (--> usdc ([] contract)); (--> (× usdt_token 6) decimal_places) becomes
    (--> (× usdt 6) decimals).
    """
    registry = MAINNET_TOKENS if registry is None else registry
    if not is_statement(statement, INHERITANCE):
        return None
    _, subject, predicate = statement
    if isinstance(predicate, tuple) and len(predicate) == 2 and predicate[0] in INT_SETS:
        predicate = predicate[1]
    if isinstance(predicate, str) and predicate.lower() in PROPERTY_SYNONYMS:
        name = _canonical_subject(subject, registry)
        if name:
            return (INHERITANCE, name, ("[]", PROPERTY_SYNONYMS[predicate.lower()]))
    if (isinstance(subject, tuple) and len(subject) == 3 and subject[0] == PRODUCT
            and isinstance(predicate, str) and predicate.lower() in RELATION_SYNONYMS
            and isinstance(subject[2], str)):
        name = _canonical_subject(subject[1], registry)
        if name:
            return (INHERITANCE, (PRODUCT, name, subject[2]), RELATION_SYNONYMS[predicate.lower()])
    return None


class EvmSource(Source):
    name = "ethereum"

    def __init__(self, transport, rpc_url: str = DEFAULT_RPC_URL,
                 registry: Optional[Dict[str, str]] = None, chain: str = "mainnet"):
        self.transport = transport
        self.rpc_url = rpc_url
        self.registry = {k.lower(): v.lower() for k, v in (registry or MAINNET_TOKENS).items()}
        self.chain = chain
        self.exact = SourceClass.PRIMARY.value
        # No known proxy slot is strong but not conclusive: Aragon, diamond and
        # bespoke proxies keep the implementation elsewhere.
        self.no_proxy_confidence = 0.8

    # --- statement shapes ---------------------------------------------------

    def _address(self, term: Term) -> Optional[str]:
        if not isinstance(term, str):
            return None
        if ADDRESS.match(term):
            return term.lower()
        return self.registry.get(term.lower())

    def _parse(self, statement: Term):
        statement = canonical_form(statement, self.registry)
        if statement is None:
            return None
        _, subject, predicate = statement
        if isinstance(predicate, tuple):
            address = self._address(subject)
            return (predicate[1], address, None, statement) if address else None
        address = self._address(subject[1])
        return (predicate, address, subject[2], statement) if address else None
    def supports(self, statement: Term) -> bool:
        return self._parse(statement) is not None

    # --- lookups ------------------------------------------------------------

    def check(self, statement: Term) -> Evidence:
        parsed = self._parse(statement)
        if parsed is None:
            return Evidence.unknown("statement shape not supported", self.name)
        kind, address, value, statement = parsed
        try:
            return getattr(self, f"_check_{kind}")(statement, address, value)
        except (TransportError, ValueError, KeyError) as exc:
            return Evidence.unknown(f"lookup failed: {exc}", self.name)

    def _check_contract(self, statement, address, _):
        code = self._rpc("eth_getCode", [address, "latest"])
        where = f"{self.chain} eth_getCode({address})"
        if code.lower().startswith(DELEGATION_PREFIX) and len(code) == 2 + 46:
            return self._evidence(False, self.exact, f"{where}: EOA with EIP-7702 delegation")
        if code in ("0x", "") or int(code, 16) == 0:
            return self._evidence(False, self.exact, f"{where}: no code")
        return self._evidence(True, self.exact, f"{where}: {(len(code) - 2) // 2} bytes of code")

    def _check_upgradeable(self, statement, address, _):
        code = self._rpc("eth_getCode", [address, "latest"])
        if code in ("0x", "") or code.lower().startswith(DELEGATION_PREFIX):
            return self._evidence(False, self.exact, f"{self.chain} {address} is not a contract")
        for label, slot in PROXY_SLOTS.items():
            word = self._rpc("eth_getStorageAt", [address, slot, "latest"])
            if int(word, 16) != 0:
                implementation = "0x" + word[-40:]
                return self._evidence(True, self.exact,
                                      f"{self.chain} {address} {label} slot -> {implementation}")
        return self._evidence(False, self.no_proxy_confidence,
                              f"{self.chain} {address} no EIP-1967/OpenZeppelin proxy slot set")

    def _check_decimals(self, statement, address, claimed):
        raw = self._rpc("eth_call", [{"to": address, "data": SELECTOR_DECIMALS}, "latest"])
        if raw in ("0x", ""):
            return Evidence.unknown(f"{address} has no decimals()", self.name)
        actual = int(raw, 16)
        provenance = f"{self.chain} {address}.decimals() = {actual}"
        if claimed.isdigit() and int(claimed) == actual:
            return self._evidence(True, self.exact, provenance)
        corrected = (INHERITANCE, (PRODUCT, statement[1][1], str(actual)), "decimals")
        return self._evidence(False, self.exact, provenance, corrected)

    def _check_symbol(self, statement, address, claimed):
        raw = self._rpc("eth_call", [{"to": address, "data": SELECTOR_SYMBOL}, "latest"])
        actual = decode_abi_string(raw)
        if not actual:
            return Evidence.unknown(f"{address} has no readable symbol()", self.name)
        provenance = f"{self.chain} {address}.symbol() = {actual}"
        if claimed.strip('"').lower() == actual.lower():
            return self._evidence(True, self.exact, provenance)
        atom = re.sub(r"[^A-Za-z0-9_.-]", "_", actual)
        corrected = (INHERITANCE, (PRODUCT, statement[1][1], atom), "symbol")
        return self._evidence(False, self.exact, provenance, corrected)

    def _evidence(self, holds: bool, confidence: float, provenance: str,
                  correction: Optional[Term] = None) -> Evidence:
        verdict = Verdict.SUPPORTS if holds else Verdict.REFUTES
        return Evidence(verdict, Truth(1.0 if holds else 0.0, confidence), self.name,
                        provenance, correction)

    def _rpc(self, method: str, params: list) -> str:
        body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
                          sort_keys=True)
        text = self.transport.request(
            "POST", self.rpc_url, body.encode("utf-8"),
            headers={"Content-Type": "application/json"},
            cache_key=f"evm:{self.chain}:{body}",
        )
        reply = json.loads(text)
        if "error" in reply:
            message = reply["error"].get("message", "")
            if method == "eth_call" and "revert" in message.lower():
                return "0x"
            raise TransportError(f"{method}: {message}")
        return reply["result"]


def decode_abi_string(raw: str) -> str:
    """Decode an ABI `string` return value, or a legacy bytes32 symbol."""
    data = bytes.fromhex(raw[2:] if raw.startswith("0x") else raw)
    if len(data) == 32:
        return data.rstrip(b"\x00").decode("utf-8", "replace")
    if len(data) < 64:
        return ""
    offset = int.from_bytes(data[0:32], "big")
    length = int.from_bytes(data[offset:offset + 32], "big")
    return data[offset + 32:offset + 32 + length].decode("utf-8", "replace")
