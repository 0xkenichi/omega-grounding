"""Stand-in for ddgs so Omega's websearch module imports; the agent run removes websearch."""


class DDGS:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def text(self, *args, **kwargs):
        raise RuntimeError("web search is disabled in this run")
