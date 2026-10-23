"""In-memory stand-in for chromadb, enough for petta_lib_chromadb to import.

Only for tools/agent_run: the real dependency (with ONNX runtime) is too large to fetch
on the machine this was run on. The agent run removes the remember/query skills, so
nothing reads from this store.
"""


class _Settings:
    def __init__(self, path):
        self.persist_directory = path


class _Collection:
    def __init__(self):
        self._rows = {}

    def add(self, ids, documents=None, embeddings=None, metadatas=None, **_):
        for i, item_id in enumerate(ids):
            self._rows[item_id] = {
                "document": (documents or [None] * len(ids))[i],
                "metadata": (metadatas or [None] * len(ids))[i],
            }

    upsert = add

    def get(self, ids=None, where=None, include=None, **_):
        keys = [k for k in (ids or self._rows) if k in self._rows]
        return {"ids": keys, "documents": [self._rows[k]["document"] for k in keys],
                "metadatas": [self._rows[k]["metadata"] for k in keys]}

    def query(self, query_embeddings=None, n_results=10, **_):
        keys = list(self._rows)[:n_results]
        return {"ids": [keys], "documents": [[self._rows[k]["document"] for k in keys]],
                "metadatas": [[self._rows[k]["metadata"] for k in keys]], "distances": [[0.0] * len(keys)]}

    def delete(self, ids=None, where=None, **_):
        for k in ids or []:
            self._rows.pop(k, None)

    def update(self, ids, metadatas=None, **_):
        for i, k in enumerate(ids):
            if k in self._rows and metadatas:
                self._rows[k]["metadata"] = metadatas[i]

    def count(self):
        return len(self._rows)


class PersistentClient:
    def __init__(self, path="./chroma_db", **_):
        self._settings = _Settings(path)
        self._collections = {}

    def get_settings(self):
        return self._settings

    def get_or_create_collection(self, name, **_):
        return self._collections.setdefault(name, _Collection())
