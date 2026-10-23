from __future__ import annotations

from abc import ABC, abstractmethod

from ..evidence import Evidence
from ..nal import Term


class Source(ABC):
    """An external authority that can confirm or refute some NAL statements."""

    name: str = "source"

    @abstractmethod
    def supports(self, statement: Term) -> bool:
        """Cheap, offline check: is this statement in the source's domain?"""

    @abstractmethod
    def check(self, statement: Term) -> Evidence:
        """Look the statement up. Never raises for lookup failures: returns UNKNOWN."""
