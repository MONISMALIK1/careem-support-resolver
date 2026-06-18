"""
Careem support policy knowledge base.
These are illustrative, paraphrased versions of public help-center rules — the
knowledge the agent retrieves from so its decisions are grounded in policy and
never invented. In production this is replaced by Careem's real help-center docs.
"""

POLICIES = [
    {
        "id": "POL-CANCEL-4.2",
        "title": "Food order cancellation fee",
        "text": ("No cancellation fee applies if a food order is cancelled before "
                 "the restaurant accepts it. Any fee charged in that case is fully "
                 "refundable to the customer."),
        "tags": ["cancel", "cancellation", "fee", "food", "restaurant", "order"],
    },
    {
        "id": "POL-REFUND-2.1",
        "title": "Refund timeline",
        "text": ("Approved refunds are returned to the original payment method "
                 "within 3-5 business days. Any refund still pending after 7 days "
                 "is escalated to priority handling."),
        "tags": ["refund", "money back", "timeline", "pending", "days"],
    },
    {
        "id": "POL-MISSING-5.3",
        "title": "Missing items",
        "text": ("For verified missing items in a delivered order, the value of the "
                 "missing items is refunded to the customer."),
        "tags": ["missing", "items", "delivery", "order", "incomplete"],
    },
    {
        "id": "POL-HOLD-3.4",
        "title": "Pre-authorization holds",
        "text": ("A pre-authorization hold may be placed on a card before a ride. "
                 "Duplicate holds are released automatically; if a duplicate is not "
                 "released within 24 hours it is refunded."),
        "tags": ["hold", "deposit", "double", "duplicate", "card", "charge", "deduct"],
    },
    {
        "id": "POL-PLUS-6.1",
        "title": "Careem Plus delivery fees",
        "text": ("Careem Plus members are not charged delivery fees on eligible "
                 "orders. A delivery fee charged in error to a Plus member is refunded."),
        "tags": ["plus", "subscription", "delivery", "fee", "member"],
    },
    {
        "id": "POL-ESCALATE-9.0",
        "title": "Human review threshold",
        "text": ("Cases involving more than AED 200, or funds held longer than 7 "
                 "days, require human review before a resolution is issued."),
        "tags": ["escalate", "human", "review", "high value", "held"],
    },
]
