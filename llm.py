"""
LLM drafting layer — the seam where a real model replaces the template.

The decision engine (agent.py) stays 100% in charge: it decides the verdict, the
amount, and the policy. The LLM's ONLY job is to phrase those already-decided
facts as a warm, human reply. It can never change a number or invent a promise —
that separation ("rules decide, model phrases") is what makes an LLM safe to put
in front of a payments flow.

Progressive enhancement: if the optional deps (openai, python-dotenv) or an
OPENROUTER_API_KEY are missing, draft_reply() returns None and the agent falls
back to its zero-setup template. So the repo always runs; the AI turns on when a
key is present.
"""
import os

# OpenRouter is a gateway that speaks the OpenAI API format but routes to Claude.
# One base_url is the only thing that makes this "OpenRouter" instead of OpenAI.
_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "anthropic/claude-sonnet-4.6"   # swap to claude-haiku-4.5 for cheaper

_SYSTEM_PROMPT = (
    "You are a Careem customer support agent. Write a short, warm, grounded reply "
    "to the customer in 3-4 sentences. You MUST only use the facts provided below. "
    "Never invent or change amounts, policies, timelines, or promises. If the "
    "verdict is not a refund, do NOT promise the customer any money. Be empathetic, "
    "clear, and concise; do not use emojis."
)


def _user_prompt(res, ticket_text, policy_text):
    lines = [
        f'The customer wrote: "{ticket_text}"',
        "",
        "Resolution decided by the system (the ONLY facts you may use):",
        f"- verdict: {res.verdict}",
    ]
    if res.verdict == "refund" and res.amount:
        lines.append(f"- refund amount: {res.currency} {res.amount:.0f}")
    if res.policy_ref:
        lines.append(f"- policy reference: {res.policy_ref}")
    if policy_text:
        lines.append(f"- what that policy says: {policy_text}")
    lines.append(f"- reason for the decision: {res.reason}")
    lines.append("")
    lines.append("Write the reply to the customer now.")
    return "\n".join(lines)


def draft_reply(res, ticket_text, policy_text="", model=DEFAULT_MODEL):
    """Return an AI-written reply string, or None if the AI layer is unavailable."""
    try:
        from openai import OpenAI
        from dotenv import load_dotenv
    except ImportError:
        return None  # deps not installed -> caller uses the template

    load_dotenv()
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        return None  # no key -> caller uses the template

    try:
        client = OpenAI(base_url=_BASE_URL, api_key=key)
        resp = client.chat.completions.create(
            model=model,
            max_tokens=512,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": _user_prompt(res, ticket_text, policy_text)},
            ],
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return None  # any API failure -> graceful fallback to the template
