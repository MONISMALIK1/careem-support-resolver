"""
Mock order / transaction store — the fact-checking layer.
The agent looks up the customer's actual order here to decide whether a complaint
is justified, instead of taking the ticket at face value. In production this is a
read-only query against Careem's order + payments systems. The money-diffing idea
is reused from my stripe-reconciler repo.
"""

ORDERS = {
    "ORD-7001": {  # food order cancelled before restaurant accepted
        "type": "food",
        "status": "cancelled",
        "restaurant_accepted": False,
        "charges": [{"type": "cancellation_fee", "amount": 70.0}],
        "currency": "AED",
        "careem_plus": False,
    },
    "ORD-7002": {  # ride with a duplicate pre-auth hold
        "type": "ride",
        "status": "completed",
        "quoted_hold": 30.0,
        "charges": [{"type": "preauth_hold", "amount": 31.0},
                    {"type": "preauth_hold", "amount": 31.0}],
        "hold_age_hours": 48,
        "currency": "AED",
        "careem_plus": False,
    },
    "ORD-7003": {  # delivered order with missing items
        "type": "food",
        "status": "delivered",
        "missing_items_value": 25.0,
        "missing_items_verified": True,
        "charges": [{"type": "order_total", "amount": 120.0}],
        "currency": "AED",
        "careem_plus": True,
    },
    "ORD-7004": {  # refund promised but not paid, 14 days ago
        "type": "ride",
        "status": "refund_approved",
        "refund_amount": 45.0,
        "refund_paid": False,
        "days_since_approved": 14,
        "currency": "AED",
        "careem_plus": False,
    },
    "ORD-7005": {  # Careem Plus member charged a delivery fee in error
        "type": "food",
        "status": "delivered",
        "charges": [{"type": "order_total", "amount": 88.0},
                    {"type": "delivery_fee", "amount": 12.0}],
        "currency": "AED",
        "careem_plus": True,
    },
    "ORD-7006": {  # high-value funds held for weeks -> must go to a human
        "type": "ride",
        "status": "disputed",
        "amount_held": 520.0,
        "days_held": 21,
        "currency": "AED",
        "careem_plus": False,
    },
}


def get_order(order_id):
    return ORDERS.get(order_id)
