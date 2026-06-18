"""
Safety guardrails — the part that makes an AI agent shippable in a payments
company. Reuses the ideas from my prompt-guard and agent-watchdog repos.

  detect_injection : block prompt-injection in customer messages so a hostile
                     ticket can't talk the agent into issuing a refund.
  Watchdog         : hard limits on steps and refund amount so the agent can
                     never loop forever or auto-approve a large payout.
"""
import re

INJECTION_PATTERNS = [
    r"ignore (all|any|previous|prior) (instructions|prompts)",
    r"you are now",
    r"system prompt",
    r"act as",
    r"disregard (the|all|your)",
    r"refund me (aed )?\d{4,}",          # demands for very large refunds
    r"approve.*without.*(checking|verifying)",
    r"pretend",
]

# No automated resolution above this amount — must go to a human.
AUTO_REFUND_CEILING_AED = 200.0
MAX_STEPS = 8


def detect_injection(text):
    t = text.lower()
    for pat in INJECTION_PATTERNS:
        if re.search(pat, t):
            return True, pat
    return False, None


class Watchdog:
    """Stops runaway agents and caps financial exposure."""

    def __init__(self, max_steps=MAX_STEPS, refund_ceiling=AUTO_REFUND_CEILING_AED):
        self.max_steps = max_steps
        self.refund_ceiling = refund_ceiling
        self.steps = 0

    def tick(self):
        self.steps += 1
        if self.steps > self.max_steps:
            raise RuntimeError("Watchdog: step limit exceeded — escalating to human")

    def within_auto_limit(self, amount):
        return amount is None or amount <= self.refund_ceiling
