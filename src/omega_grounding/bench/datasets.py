from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..nal import INHERITANCE, Term, is_statement, normalize, parse, reverse
from ..sources.evm import canonical_form


@dataclass(frozen=True)
class Item:
    id: str
    domain: str
    text: str
    statement: Term
    gold: bool
    also_true: Tuple[Term, ...] = field(default=())
    # Answer-type items: the statement is the one right value, any other value
    # for the same subject and relation is false.
    exclusive: bool = False

    @property
    def swappable(self) -> bool:
        """Relation swaps only make sense between two plain terms."""
        return (is_statement(self.statement, INHERITANCE)
                and all(isinstance(t, str) for t in self.statement[1:]))

    def truth_of(self, statement: Term) -> Optional[bool]:
        """World truth of a statement an LLM or the grounder produced for this item.

        The reverse of a dataset inheritance is false: every pair here is a
        proper class relation. None means the statement cannot be graded.
        """
        n = _comparable(statement)
        if n == _comparable(self.statement):
            return self.gold
        if self.swappable and n == _comparable(reverse(self.statement)):
            return False
        if n in {_comparable(t) for t in self.also_true}:
            return True
        if self.exclusive and _same_relation_other_value(n, _comparable(self.statement)):
            return False
        return None


def _same_relation_other_value(a: Term, b: Term) -> bool:
    """(--> (× s v1) r) vs (--> (× s v2) r) with v1 != v2."""
    def parts(t):
        if (is_statement(t, INHERITANCE) and isinstance(t[1], tuple) and len(t[1]) == 3):
            return t[1][1], t[2], t[1][2]
        return None
    pa, pb = parts(a), parts(b)
    return bool(pa and pb and pa[:2] == pb[:2] and pa[2] != pb[2])


def _comparable(statement: Term) -> Term:
    """Equivalent phrasings of an on-chain fact compare equal; everything else case-folded."""
    return normalize(canonical_form(statement) or statement)


@dataclass(frozen=True)
class Chain:
    id: str
    premises: Tuple[str, ...]
    conclusion: Term
    gold: bool


def load_items(directory: Path, domains: List[str]) -> Dict[str, Item]:
    items: Dict[str, Item] = {}
    for domain in domains:
        for line in (Path(directory) / f"{domain}.jsonl").read_text().splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            items[row["id"]] = Item(
                id=row["id"], domain=domain, text=row["text"], statement=parse(row["statement"]),
                gold=row["gold"], also_true=tuple(parse(t) for t in row.get("also_true", [])),
                exclusive=row.get("exclusive", False),
            )
    return items


def load_chains(directory: Path, items: Dict[str, Item]) -> List[Chain]:
    path = Path(directory) / "chains.jsonl"
    chains = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if all(p in items for p in row["premises"]):
            chains.append(Chain(row["id"], tuple(row["premises"]), parse(row["conclusion"]), row["gold"]))
    return chains
