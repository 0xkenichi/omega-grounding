"""Build benchmark/datasets/onchain_longtail.jsonl: open questions about token decimals.

    python tools/build_longtail_dataset.py uniswap-tokens.json

The model must answer ("How many decimals does ... use?") rather than restate a claim,
which is where LLMs guess. Gold values come from the token list and are checked
against the chain when the benchmark records its sources (coverage table).
Every token with non-18 decimals is included, plus a seeded sample of 18-decimal ones.
"""

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = json.loads((ROOT / "src" / "omega_grounding" / "sources" / "tokens_mainnet.json").read_text())["tokens"]
CORE = {"usdc", "usdt", "dai", "weth", "link", "uni", "steth", "aave_v3_pool"}  # already in onchain.jsonl
OUT = ROOT / "benchmark" / "datasets" / "onchain_longtail.jsonl"


def main(path: str, n_eighteen: int = 15, seed: int = 0) -> None:
    tokens = [t for t in json.loads(Path(path).read_text())["tokens"] if t["chainId"] == 1]
    eligible = [t for t in tokens
                if REGISTRY.get(t["symbol"].lower()) == t["address"].lower() and t["symbol"].lower() not in CORE]
    odd = sorted((t for t in eligible if t["decimals"] != 18), key=lambda t: t["symbol"].lower())
    eighteen = sorted((t for t in eligible if t["decimals"] == 18), key=lambda t: t["symbol"].lower())
    picked = odd + random.Random(seed).sample(eighteen, n_eighteen)
    with OUT.open("w") as out:
        for i, t in enumerate(picked, 1):
            symbol = t["symbol"].lower()
            out.write(json.dumps({
                "id": f"L{i:02d}",
                "text": f"How many decimals does the {t['name']} ({t['symbol']}) ERC-20 token at "
                        f"{t['address']} on Ethereum mainnet use?",
                "statement": f"(--> (× {symbol} {t['decimals']}) decimals)",
                "gold": True,
                "exclusive": True,
            }, ensure_ascii=False) + "\n")
    print(f"wrote {len(picked)} questions ({len(odd)} non-18-decimal, {n_eighteen} 18-decimal) to {OUT}")


if __name__ == "__main__":
    main(sys.argv[1])
