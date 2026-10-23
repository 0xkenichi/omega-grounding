"""Build the bundled Ethereum token registry from a Uniswap-format token list.

    python tools/build_token_registry.py uniswap-tokens.json

Writes src/omega_grounding/sources/tokens_mainnet.json: lowercase symbol -> address for
chainId 1. Symbols that are ambiguous (two addresses) or not plain atoms are skipped.
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "src" / "omega_grounding" / "sources" / "tokens_mainnet.json"
ATOM = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")


def main(path: str) -> None:
    data = json.loads(Path(path).read_text())
    by_symbol = defaultdict(set)
    for token in data["tokens"]:
        if token["chainId"] == 1:
            by_symbol[token["symbol"].lower()].add(token["address"].lower())
    tokens = {s: next(iter(a)) for s, a in sorted(by_symbol.items()) if len(a) == 1 and ATOM.match(s)}
    version = data.get("version", {})
    OUT.write_text(json.dumps({
        "source": f"{data.get('name')} token list v{version.get('major')}.{version.get('minor')}.{version.get('patch')}",
        "url": "https://tokens.uniswap.org",
        "tokens": tokens,
    }, indent=1, sort_keys=True) + "\n")
    skipped = len(by_symbol) - len(tokens)
    print(f"wrote {len(tokens)} tokens to {OUT} ({skipped} ambiguous or non-atom symbols skipped)")


if __name__ == "__main__":
    main(sys.argv[1])
