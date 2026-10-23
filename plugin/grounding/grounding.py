"""py-call entry points for grounding.metta.

The logic lives in the omega_grounding package, installed into Omega's Python
environment (see README.md); this module only re-exports what MeTTa calls.
"""

from omega_grounding.bridge import ground, lookup, to_float

__all__ = ["ground", "lookup", "to_float"]
