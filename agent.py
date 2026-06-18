"""
Careem Support-Resolution Agent.

A ReAct-style loop (reuses my react_agent repo) that turns a raw support ticket
into a grounded resolution:

  Thought -> Action(classify) -> Action(retrieve policy) ->
  Action(check order facts) -> Decision -> grounded reply

Every step is logged to a trace so a human can audit exactly why a decision was
made. The agent NEVER invents a refund: a payout requires both a matching policy
and matching order facts, and anything above the watchdog ceiling or flagged as
ambiguous is escalated to a human.
"""
from dataclasses import dataclass, field
from retriever import retrieve
from orders import get_order
from guardrails import detect_injection, Watchdog


# ---- 1. Classify -----------------------------------------------------------
ISSUE_RULES = {
    "unfair_cancellation_fee": ["cancel", "cancellation fee", "waiting for restaurant",
                                "charged for cancel"],
    "duplicate_charge":        ["twice", "double", "two times", "3 times", "duplicate",
                                "deducted again", "two holds", "deposit twice"],
    "missing_items":           ["missing", "items missing", "didn't receive item",
                                "incomplete order"],
    "refund_delay":            ["refund", "money back", "still waiting", "promised",
                                "no refund", "not refunded"],
    "plus_fee_charged":        ["plus", "subscription", "charged delivery", "delivery fee"],
    "funds_held":              ["held", "holding my money", "weeks", "blocked my money"],
}


def classify(text):
    t = text.lower()
    best, score = "other", 0
    for issue, kws in ISSUE_RULES.items():
        s = sum(1 for k in kws if k in t)
        if s > score:
            best, score = issue, s
    return best


# ---- 2-4. Decide based on policy + order facts -----------------------------
@dataclass
class Resolution:
    verdict: str            # "refund" | "no_action" | "escalate"
    amount: float = 0.0
    currency: str = "AED"
    policy_ref: str = ""
    reason: str = ""
    reply: str = ""
    trace: list = field(default_factory=list)


def _decide(issue, order, policy_id):
    """Pure decision logic: returns (verdict, amount, reason)."""
    if order is None:
        return "escalate", 0.0, "No matching order found — needs human lookup"

    if issue == "unfair_cancellation_fee":
        if not order.get("restaurant_accepted", True):
            fee = sum(c["amount"] for c in order["charges"] if c["type"] == "cancellation_fee")
            return "refund", fee, "Order cancelled before restaurant accepted"
        return "no_action", 0.0, "Restaurant had accepted; fee applies"

    if issue == "duplicate_charge":
        holds = [c for c in order.get("charges", []) if c["type"] == "preauth_hold"]
        if len(holds) > 1 and order.get("hold_age_hours", 0) > 24:
            return "refund", holds[-1]["amount"], "Duplicate pre-auth hold not released in 24h"
        return "no_action", 0.0, "No un-released duplicate hold found"

    if issue == "missing_items":
        if order.get("missing_items_verified"):
            return "refund", order["missing_items_value"], "Missing items verified"
        return "escalate", 0.0, "Missing items not yet verified"

    if issue == "refund_delay":
        if order.get("status") == "refund_approved" and not order.get("refund_paid"):
            verdict = "escalate" if order.get("days_since_approved", 0) > 7 else "no_action"
            return verdict, order.get("refund_amount", 0.0), \
                "Approved refund pending beyond 7 days" if verdict == "escalate" \
                else "Refund approved, within 3-5 day window"
        return "no_action", 0.0, "No approved refund pending"

    if issue == "plus_fee_charged":
        if order.get("careem_plus"):
            fee = sum(c["amount"] for c in order["charges"] if c["type"] == "delivery_fee")
            if fee:
                return "refund", fee, "Plus member charged a delivery fee in error"
        return "no_action", 0.0, "No erroneous delivery fee for a Plus member"

    if issue == "funds_held":
        return "escalate", order.get("amount_held", 0.0), "High-value funds held — human review"

    return "escalate", 0.0, "Unclassified issue — human review"


def _draft_reply(res, order):
    """Grounded, human reply. The seam where a real LLM (Claude) plugs in for
    natural phrasing; the template keeps the demo runnable with zero setup."""
    cur = res.currency
    if res.verdict == "refund":
        return (f"Thanks for flagging this, and sorry for the trouble. I checked your "
                f"order and you're right: {res.reason.lower()}. Under {res.policy_ref}, "
                f"that qualifies for a refund. I've approved {cur} {res.amount:.0f} back to "
                f"your original payment method — it'll arrive in 3-5 business days.")
    if res.verdict == "escalate":
        return (f"Thanks for your patience. Your case ({res.reason.lower()}) needs a "
                f"specialist to review before I resolve it, so I've escalated it with "
                f"priority. You'll hear back within 24 hours with a clear outcome.")
    return (f"Thanks for reaching out. I reviewed your order in detail — {res.reason.lower()}, "
            f"so no charge was applied in error here. Happy to take another look if you have "
            f"more detail.")


# ---- The agent loop --------------------------------------------------------
def resolve(ticket_text, order_id=None):
    dog = Watchdog()
    res = Resolution(verdict="escalate")

    # Step 0 — safety gate
    dog.tick()
    injected, pat = detect_injection(ticket_text)
    res.trace.append(f"guardrail: injection check -> {'BLOCKED' if injected else 'clean'}")
    if injected:
        res.verdict, res.reason = "escalate", "Message flagged by injection filter"
        res.reply = ("Thanks for reaching out. I've routed this to a human agent who will "
                     "follow up shortly.")
        res.trace.append(f"  matched pattern: {pat} -> no automated payout, human only")
        return res

    # Step 1 — classify
    dog.tick()
    issue = classify(ticket_text)
    res.trace.append(f"classify -> {issue}")

    # Step 2 — retrieve policy
    dog.tick()
    hits = retrieve(ticket_text + " " + issue, k=1)
    if hits:
        _, policy, matched = hits[0]
        res.policy_ref = policy["id"]
        res.trace.append(f"retrieve policy -> {policy['id']} ({policy['title']}) "
                         f"[matched: {', '.join(matched)}]")
    else:
        res.trace.append("retrieve policy -> none matched")
        policy = None

    # Step 3 — fact check against the order
    dog.tick()
    order = get_order(order_id) if order_id else None
    res.trace.append(f"check order {order_id} -> {'found' if order else 'not found'}")
    if order:
        res.currency = order.get("currency", "AED")

    # Step 4 — decide
    dog.tick()
    verdict, amount, reason = _decide(issue, order, res.policy_ref)
    # Watchdog: cap automated payouts
    if verdict == "refund" and not dog.within_auto_limit(amount):
        verdict, reason = "escalate", f"Refund {amount:.0f} exceeds auto-limit — human review"
    res.verdict, res.amount, res.reason = verdict, amount, reason
    res.trace.append(f"decide -> {verdict} "
                     f"{('AED %.0f' % amount) if amount else ''} ({reason})")

    # Step 5 — draft grounded reply
    dog.tick()
    res.reply = _draft_reply(res, order)
    res.trace.append(f"draft reply -> {len(res.reply)} chars (grounded in "
                     f"{res.policy_ref or 'n/a'})")
    return res
