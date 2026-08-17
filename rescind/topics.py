"""Topic-anchored deterministic vectors -- offline scaffolding, stated plainly.

WHAT THIS IS: a stand-in for Titan embeddings used when no AWS credentials are
present (CI, and the recorded demo). Each named topic gets its own dedicated
axis, so a fact and a question that share topics land close together by
construction, and the retrieval/threshold/refusal paths exercise exactly as they
would with real embeddings.

WHAT THIS IS NOT: semantics. These vectors encode the topic labels the seed
script assigns, not the meaning of the text. With AWS credentials the identical
code path calls amazon.titan-embed-text-v2:0 instead and nothing else changes --
the vectors are the only substituted component.

This is written down here, in docs/LIMITS.md, and in the README rather than
being quietly hidden inside a fallback, because a demo that silently fabricates
its own inputs is the failure mode this project exists to argue against.
"""

from __future__ import annotations

import math
from typing import Mapping

from .config import EMBED_DIM

# Explicit axis assignment -- no hashing, so no accidental collisions between
# two topics landing on the same dimension.
TOPIC_AXES: dict[str, int] = {
    "lot_release_safety": 0,
    "supplier_standing": 1,
    "microbiological_testing": 2,
    "cold_chain": 3,
    "supplier_audit": 4,
    "regulatory_notice": 5,
    "logistics": 6,
    "packaging": 7,
}


def topic_vector(topics: Mapping[str, float]) -> list[float]:
    """Build a unit vector from a topic -> weight mapping."""
    if not topics:
        raise ValueError("at least one topic is required")
    unknown = set(topics) - set(TOPIC_AXES)
    if unknown:
        raise ValueError(f"unknown topics: {sorted(unknown)}")

    vec = [0.0] * EMBED_DIM
    for topic, weight in topics.items():
        vec[TOPIC_AXES[topic]] += float(weight)

    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0.0:
        raise ValueError("topic weights produced a zero vector")
    return [v / norm for v in vec]
