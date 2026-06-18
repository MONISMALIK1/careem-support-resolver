"""
Transparent policy retriever (the RAG layer).
Scores each policy by keyword overlap with the ticket — every match is
explainable, no black box. In production swap this for an embedding search over
Careem's help center (the agent interface stays identical). Mirrors the approach
in my corrective_rag / self_rag repos.
"""
import re
from policies import POLICIES


def _tokens(text):
    return set(re.findall(r"[a-z]+", text.lower()))


def retrieve(query, k=2):
    q = _tokens(query)
    scored = []
    for p in POLICIES:
        hits = q & set(p["tags"])
        if hits:
            scored.append((len(hits), p, sorted(hits)))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:k]
