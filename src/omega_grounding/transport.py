"""HTTP access for sources, with record/replay cassettes.

Cassettes make the benchmark deterministic and runnable offline: record once
against the live services, commit the cassette, replay everywhere else.
A source may pass `compact` to keep only the part of a response it needs;
it is applied before the response is returned or recorded.
"""

from __future__ import annotations

import hashlib
import json
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable, Dict, Optional

DEFAULT_USER_AGENT = "omega-grounding/0.1 (Omega premise-grounding research benchmark)"
Compact = Optional[Callable[[str], str]]


class TransportError(RuntimeError):
    pass


class CassetteMiss(TransportError):
    pass


class HttpTransport:
    """urllib with a polite request interval and backoff on 429/503."""

    def __init__(self, timeout: float = 60.0, min_interval: float = 0.0,
                 retries: int = 5, max_backoff: float = 60.0):
        self.timeout = timeout
        self.min_interval = min_interval
        self.retries = retries
        self.max_backoff = max_backoff
        self._last = 0.0

    def request(self, method: str, url: str, body: Optional[bytes] = None,
                headers: Optional[Dict[str, str]] = None,
                cache_key: Optional[str] = None, compact: Compact = None,
                store: bool = True) -> str:
        merged = {"User-Agent": DEFAULT_USER_AGENT, **(headers or {})}
        for attempt in range(self.retries + 1):
            wait = self.min_interval - (time.monotonic() - self._last)
            if wait > 0:
                time.sleep(wait)
            req = urllib.request.Request(url, data=body, method=method, headers=merged)
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    text = resp.read().decode("utf-8")
                return compact(text) if compact else text
            except urllib.error.HTTPError as exc:
                if exc.code not in (429, 503) or attempt == self.retries:
                    raise TransportError(f"{method} {url}: {exc}") from exc
                time.sleep(self._backoff(exc.headers.get("Retry-After"), attempt))
            except Exception as exc:  # urllib raises several unrelated types
                raise TransportError(f"{method} {url}: {exc}") from exc
            finally:
                self._last = time.monotonic()
        raise TransportError(f"{method} {url}: retries exhausted")

    # No cache: every lookup goes to the network.
    def cached(self, cache_key: str) -> Optional[str]:
        return None

    def remember(self, cache_key: str, response: str) -> None:
        pass

    def _backoff(self, retry_after: Optional[str], attempt: int) -> float:
        try:
            return min(float(retry_after), self.max_backoff)
        except (TypeError, ValueError):
            return min(2.0 ** (attempt + 1), self.max_backoff)


class CassetteTransport:
    """Replay recorded responses, or record live ones (mode='record')."""

    def __init__(self, path: Path, mode: str = "replay", inner: Optional[HttpTransport] = None):
        if mode not in ("replay", "record"):
            raise ValueError(f"unknown cassette mode {mode!r}")
        if path is None:
            raise ValueError(f"cassette mode {mode!r} needs a cassette path")
        self.path = Path(path)
        self.mode = mode
        self.inner = inner or HttpTransport()
        self._data: Dict[str, dict] = {}
        self._dirty = 0
        if self.path.exists():
            self._data = json.loads(self.path.read_text())["interactions"]

    @staticmethod
    def key(method: str, url: str, body: Optional[bytes], cache_key: Optional[str]) -> str:
        material = cache_key or f"{method} {url} {(body or b'').decode('utf-8')}"
        return hashlib.sha256(material.encode("utf-8")).hexdigest()[:24]

    def request(self, method: str, url: str, body: Optional[bytes] = None,
                headers: Optional[Dict[str, str]] = None,
                cache_key: Optional[str] = None, compact: Compact = None,
                store: bool = True) -> str:
        """store=False: fetch through (or fail in replay) without recording."""
        key = self.key(method, url, body, cache_key)
        if key in self._data:
            return self._data[key]["response"]
        if self.mode == "replay":
            raise CassetteMiss(f"no recorded response for {cache_key or url} in {self.path}")
        response = self.inner.request(method, url, body, headers, compact=compact)
        if store:
            self._store(key, cache_key or f"{method} {url}", response)
        return response

    # Per-key access, for sources that fetch in batches but record per item
    # (batch composition varies between runs; items do not).
    def cached(self, cache_key: str) -> Optional[str]:
        entry = self._data.get(self.key("", "", None, cache_key))
        return entry["response"] if entry else None

    def remember(self, cache_key: str, response: str) -> None:
        self._store(self.key("", "", None, cache_key), cache_key, response)

    def _store(self, key: str, request: str, response: str) -> None:
        self._data[key] = {"request": request, "response": response}
        self._dirty += 1
        if self._dirty >= 25:
            self.save()

    def save(self) -> None:
        if not self._dirty and self.path.exists():
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"version": 1, "interactions": dict(sorted(self._data.items()))}
        self.path.write_text(json.dumps(payload, indent=1, ensure_ascii=False) + "\n")
        self._dirty = 0
