"""
Demo runner. Feeds the sample tickets through the agent and prints, for each:
the reasoning trace, the decision, and the customer-facing reply.

Run:  python3 main.py
Zero dependencies.
"""
from agent import resolve
from tickets import SAMPLE_TICKETS

W = 76
VERDICT_LABEL = {"refund": "REFUND APPROVED", "no_action": "NO ACTION NEEDED",
                 "escalate": "ESCALATED TO HUMAN"}


def main():
    print("=" * W)
    print("  CAREEM SUPPORT-RESOLUTION AGENT — demo")
    print("  resolves the #1 customer complaint (failed support) in seconds")
    print("=" * W)

    refunds = 0
    total_refunded = 0.0
    for i, (ticket, order_id) in enumerate(SAMPLE_TICKETS, 1):
        res = resolve(ticket, order_id)
        print(f"\nTICKET {i}  (order {order_id})")
        print(f'  customer: "{ticket}"')
        print("  --- agent reasoning ---")
        for step in res.trace:
            print(f"    . {step}")
        label = VERDICT_LABEL.get(res.verdict, res.verdict)
        money = f"  |  AED {res.amount:.0f}" if res.verdict == "refund" and res.amount else ""
        print(f"  >> {label}{money}")
        print(f"  reply: {res.reply}")
        if res.verdict == "refund" and res.amount:
            refunds += 1
            total_refunded += res.amount
        print("-" * W)

    print(f"\nSUMMARY: {len(SAMPLE_TICKETS)} tickets handled · {refunds} auto-refunds "
          f"approved (AED {total_refunded:.0f}) · rest correctly escalated or closed.")
    print("Every decision is grounded in a policy + the order facts, with an "
          "injection guard\nand a refund ceiling. Resolution time: seconds, not weeks.")


if __name__ == "__main__":
    main()
