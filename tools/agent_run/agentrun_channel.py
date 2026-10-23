"""Omega plugin for tools/agent_run: a scripted chat channel plus the inference guard.

The channel ("script") feeds the user messages from $AGENT_RUN_SCRIPT one at a time,
moving to the next once the agent has replied and gone quiet (or after a timeout),
and logs every message in both directions to $AGENT_RUN_TRANSCRIPT as JSON lines.
"""

import json
import os
import time

import channels
from agentrun_guard import allowed_inference  # noqa: F401  (called from agentrun_safety.metta)

QUIET_SECONDS = 25.0


class ScriptChannel(channels.CommChannel):
    def start(self) -> None:
        with open(os.environ["AGENT_RUN_SCRIPT"]) as f:
            self.messages = json.load(f)["messages"]
        self.transcript = os.environ["AGENT_RUN_TRANSCRIPT"]
        self.timeout = float(os.environ.get("AGENT_RUN_MESSAGE_TIMEOUT", "240"))
        self.index = -1
        self.delivered_at = 0.0
        self.last_reply_at = None
        self._log("channel", "started")

    def stop(self) -> None:
        self._log("channel", "stopped")

    def receive(self) -> str:
        now = time.time()
        if self.index + 1 < len(self.messages) and self._ready_for_next(now):
            self.index += 1
            self.delivered_at = now
            self.last_reply_at = None
            self._log("user", self.messages[self.index])
        return self.messages[self.index] if self.index >= 0 else ""

    def _ready_for_next(self, now: float) -> bool:
        if self.index < 0:
            return True
        if self.last_reply_at is not None and now - self.last_reply_at > QUIET_SECONDS:
            return True
        return now - self.delivered_at > self.timeout

    def send(self, message: str) -> None:
        self.last_reply_at = time.time()
        self._log("agent", message)

    def _log(self, role: str, text: str) -> None:
        with open(self.transcript, "a") as f:
            f.write(json.dumps({"t": round(time.time(), 1), "role": role, "text": text,
                                "message_index": self.index}) + "\n")


def loadOmegaPlugin():
    channels.registerCommChannel("script", ScriptChannel())
