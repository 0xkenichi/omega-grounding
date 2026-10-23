from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..nal import INHERITANCE, Term, is_statement, normalize, parse, reverse


@dataclass(frozen=True)
class Item:
    id: str
    domain: str
    text: str
    statement: Term
    gold: bool
    also_true: Tuple[Term, ...] = field(default=())

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
        n = normalize(statement)
        if n == normalize(self.statement):
            return self.gold
        if self.swappable and n == normalize(reverse(self.statement)):
            return False
        if n in {normalize(t) for t in self.also_true}:
            return True
        return None


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
