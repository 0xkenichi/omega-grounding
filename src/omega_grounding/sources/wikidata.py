"""Wikidata as a source for taxonomic inheritance: (--> dolphin mammal).

A term can name several items ("dolphin": the animal, a surname, a KDE file
manager), so every item whose English label or alias matches the term exactly
is a candidate sense. The statement is supported when some sense of the
subject reaches some sense of the predicate through instance-of (first step
only), subclass-of or parent-taxon links. If only the reverse holds, the
relation was swapped: the statement is refuted and a correction is offered.

The graph is walked with the entity API in batches, recorded per item so
cassette keys stay stable, rather than the SPARQL endpoint, which is often
rate-limited.
"""

from __future__ import annotations

import json
import re
import urllib.parse
from typing import Dict, List, Optional, Set, Tuple

from ..evidence import Evidence, SourceClass, Verdict
from ..nal import INHERITANCE, Term, Truth, is_statement, reverse
from ..transport import DEFAULT_USER_AGENT, TransportError
from .base import Source

API_URL = "https://www.wikidata.org/w/api.php"
INSTANCE_OF, SUBCLASS_OF, PARENT_TAXON = "P31", "P279", "P171"
QID = re.compile(r"^Q[1-9][0-9]*$", re.IGNORECASE)
ATOM = re.compile(r"^[A-Za-z][A-Za-z0-9_'-]*$")


def compact_entity(text: str) -> str:
    """Keep only the parent links of an entity response, to keep cassettes small."""
    data = json.loads(text)
    out = {}
    for qid, entity in data.get("entities", {}).items():
        links = {}
        for prop in (INSTANCE_OF, SUBCLASS_OF, PARENT_TAXON):
            ids = []
            for claim in entity.get("claims", {}).get(prop, []):
                snak = claim.get("mainsnak", {})
                if claim.get("rank") != "deprecated" and snak.get("snaktype") == "value":
                    ids.append(snak["datavalue"]["value"]["id"])
            links[prop] = ids
        out[qid] = {"label": entity.get("labels", {}).get("en", {}).get("value", qid), "links": links}
    return json.dumps(out, sort_keys=True)


def compact_search(text: str) -> str:
    hits = json.loads(text).get("search", [])
    return json.dumps([{"id": h["id"], "label": h.get("label", ""),
                        "match": h.get("match", {}).get("text", ""),
                        "type": h.get("match", {}).get("type", "")} for h in hits])


class WikidataSource(Source):
    name = "wikidata"

    def __init__(self, transport, closed_world: bool = True,
                 closed_world_confidence: float = SourceClass.VERIFIED_SECONDARY.value,
                 user_agent: str = DEFAULT_USER_AGENT, max_senses: int = 5, max_nodes: int = 400,
                 max_generic_hops: int = 3):
        self.transport = transport
        # Absence of a path between resolved items is weak evidence. Off =
        # open world (UNKNOWN). With the default 0.7 it demotes an LLM
        # assertion below ACT when the LLM's confidence is under ~0.93
        # (0.78 after the discount), and never flips it to a confident denial.
        self.closed_world = closed_world
        self.closed_world_confidence = closed_world_confidence
        self.headers = {"User-Agent": user_agent, "Accept": "application/json"}
        self.confidence = SourceClass.VERIFIED_SECONDARY.value
        self.max_senses = max_senses
        self.max_nodes = max_nodes
        self.max_generic_hops = max_generic_hops
        self._entities: Dict[str, dict] = {}
        self._labels: Dict[str, str] = {}

    def supports(self, statement: Term) -> bool:
        return (is_statement(statement, INHERITANCE)
                and all(isinstance(t, str) and ATOM.match(t) and not t.lower().startswith("0x")
                        for t in statement[1:]))

    def check(self, statement: Term) -> Evidence:
        try:
            return self._check(statement)
        except (TransportError, ValueError, KeyError) as exc:
            return Evidence.unknown(f"lookup failed: {exc}", self.name)

    def _check(self, statement: Term) -> Evidence:
        _, subject, predicate = statement
        subjects, predicates = self.senses(subject), self.senses(predicate)
        missing = [t for t, s in ((subject, subjects), (predicate, predicates)) if not s]
        if missing:
            return Evidence.unknown(f"no Wikidata item labelled {', '.join(missing)}", self.name)
        found = self._reaches(subjects, predicates)
        if found:
            return Evidence(Verdict.SUPPORTS, Truth(1.0, self.confidence), self.name,
                            f"{self._describe(found)} via P31/P279/P171")
        found = self._reaches(predicates, subjects)
        if found:
            return Evidence(Verdict.REFUTES, Truth(0.0, self.confidence), self.name,
                            f"only the reverse holds: {self._describe(found)}",
                            correction=reverse(statement))
        tried = f"{len(subjects)} x {len(predicates)} senses of {subject}, {predicate}"
        if self.closed_world:
            return Evidence(Verdict.REFUTES, Truth(0.0, self.closed_world_confidence), self.name,
                            f"no class or taxon path between {tried} (closed-world)")
        return Evidence.unknown(f"no path between {tried}", self.name)

    # --- lookups ------------------------------------------------------------

    def senses(self, term: str) -> List[str]:
        if QID.match(term):
            return [term.upper()]
        label = term.replace("_", " ").lower()
        params = urllib.parse.urlencode({
            "action": "wbsearchentities", "search": label, "language": "en",
            "uselang": "en", "type": "item", "limit": 30, "format": "json",
        })
        hits = json.loads(self.transport.request(
            "GET", f"{API_URL}?{params}", headers=self.headers,
            cache_key=f"wikidata:search:{label}", compact=compact_search))
        exact = []
        for rank, hit in enumerate(hits):
            if hit["match"].lower() == label and hit["id"] not in self._labels:
                self._labels[hit["id"]] = hit["label"] or label
            if hit["match"].lower() == label and all(hit["id"] != e[2] for e in exact):
                exact.append((hit.get("type") != "label", rank, hit["id"]))
        self._fetch([qid for _, _, qid in exact])

        # Items in a taxon tree first, then other classes, then one-off
        # instances (people, films, surnames); label matches before aliases,
        # then search rank. Taxa are often found only by alias: "reptile" is
        # an alias of Reptilia, while a game character has it as its label.
        def key(entry):
            alias, rank, qid = entry
            links = self._entities[qid]["links"]
            kind = 0 if links.get(PARENT_TAXON) else 1 if links.get(SUBCLASS_OF) else 2
            return (kind, alias, rank)

        return [qid for _, _, qid in sorted(exact, key=key)][: self.max_senses]

    def _fetch(self, qids: List[str]) -> None:
        """Load parent links for items, from the cassette or in batches of 50."""
        missing = []
        for qid in dict.fromkeys(qids):
            if qid in self._entities:
                continue
            cached = self.transport.cached(f"wikidata:entity:{qid}")
            if cached is None:
                missing.append(qid)
            else:
                self._entities[qid] = json.loads(cached).get(qid, {"label": qid, "links": {}})
        for i in range(0, len(missing), 50):
            chunk = missing[i:i + 50]
            params = urllib.parse.urlencode({
                "action": "wbgetentities", "ids": "|".join(chunk), "props": "claims|labels",
                "languages": "en", "format": "json",
            })
            batch = json.loads(self.transport.request(
                "GET", f"{API_URL}?{params}", headers=self.headers,
                cache_key=f"wikidata:batch:{'|'.join(chunk)}", compact=compact_entity, store=False))
            for qid in chunk:
                entity = batch.get(qid, {"label": qid, "links": {}})
                self._entities[qid] = entity
                self.transport.remember(f"wikidata:entity:{qid}", json.dumps({qid: entity}, sort_keys=True))

    def _reaches(self, starts: List[str], goals: List[str]) -> Optional[Tuple[str, str]]:
        """Level-by-level walk up from any start to any goal.

        Beyond the first step, a taxon (an item with a parent taxon) is left by
        parent-taxon links only, so biological claims are judged on the taxon
        tree and cannot leak through folk or clade-mixing classes higher up
        (Cetacea is a subclass of fish in Wikidata). Statements made directly
        on the subject item are always followed. Elsewhere,
        instance-of (first step only) and subclass-of links cost one hop each,
        capped at `max_generic_hops` so the walk stays out of the upper ontology.
        """
        goal_set: Set[str] = set(goals)
        for start in starts:
            if start in goal_set:
                return start, start
        frontier = [(s, s, 0, True) for s in starts]
        seen: Set[str] = set(starts)
        while frontier and len(seen) < self.max_nodes:
            self._fetch([node for node, _, _, _ in frontier])
            following = []
            for node, origin, hops, first in frontier:
                links = self._entities[node]["links"]
                edges = [(q, 0) for q in links.get(PARENT_TAXON, [])]
                if first or not edges:
                    edges += [(q, 1) for q in links.get(SUBCLASS_OF, [])]
                if first:
                    edges += [(q, 1) for q in links.get(INSTANCE_OF, [])]
                for parent, cost in edges:
                    if hops + cost > self.max_generic_hops:
                        continue
                    if parent in goal_set:
                        return origin, parent
                    if parent not in seen:
                        seen.add(parent)
                        following.append((parent, origin, hops + cost, False))
            frontier = following
        return None

    def _label(self, qid: str) -> str:
        if qid in self._labels:
            return self._labels[qid]
        return self._entities.get(qid, {}).get("label", qid)

    def _describe(self, pair: Tuple[str, str]) -> str:
        a, b = pair
        return f"{a} ({self._label(a)}) -> {b} ({self._label(b)})"
