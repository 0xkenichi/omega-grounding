"""In-memory stand-ins for Wikidata and an Ethereum node."""

import json
import urllib.parse


class FakeTransport:
    def __init__(self, handler):
        self.handler = handler
        self.requests = []

    def request(self, method, url, body=None, headers=None, cache_key=None, compact=None, store=True):
        self.requests.append(cache_key or url)
        text = self.handler(method, url, body)
        return compact(text) if compact else text

    def cached(self, cache_key):
        return None

    def remember(self, cache_key, response):
        pass


def wikidata(labels, links):
    """labels: term -> [(qid, label, match_type)], links: qid -> {prop: [qids]}."""

    def handler(method, url, body):
        query = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(url).query))
        if query["action"] == "wbsearchentities":
            hits = [{"id": q, "label": lab, "match": {"type": kind, "text": query["search"]}}
                    for q, lab, kind in labels.get(query["search"], [])]
            return json.dumps({"search": hits})
        entities = {}
        for qid in query["ids"].split("|"):
            claims = {prop: [{"rank": "normal", "mainsnak": {"snaktype": "value",
                                                              "datavalue": {"value": {"id": t}}}}
                             for t in targets]
                      for prop, targets in links.get(qid, {}).items()}
            entities[qid] = {"labels": {"en": {"value": qid}}, "claims": claims}
        return json.dumps({"entities": entities})

    return FakeTransport(handler)


def ethereum(code=None, storage=None, calls=None):
    """code: addr -> hex, storage: (addr, slot) -> hex word, calls: (addr, selector) -> hex."""
    code, storage, calls = code or {}, storage or {}, calls or {}

    def handler(method, url, body):
        req = json.loads(body)
        m, p = req["method"], req["params"]
        if m == "eth_getCode":
            result = code.get(p[0], "0x")
        elif m == "eth_getStorageAt":
            result = storage.get((p[0], p[1]), "0x" + "0" * 64)
        elif m == "eth_call":
            result = calls.get((p[0]["to"], p[0]["data"]), "0x")
        else:
            raise AssertionError(m)
        return json.dumps({"jsonrpc": "2.0", "id": 1, "result": result})

    return FakeTransport(handler)
