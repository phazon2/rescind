"""Rescind -- retractable agent memory on CockroachDB.

When a lot is recalled, Rescind pulls back every conclusion the agent built on
it -- in one transaction, with proof of what the agent knew before and after.
"""

__version__ = "0.1.0"

from .agent import Decision, ask, open_reviews
from .memory import (
    Recalled,
    RetractionReceipt,
    ReplayReport,
    assert_fact,
    derive_fact,
    recall_lot,
    replay,
    retract,
    retrieve,
)

__all__ = [
    "Decision",
    "Recalled",
    "ReplayReport",
    "RetractionReceipt",
    "ask",
    "assert_fact",
    "derive_fact",
    "open_reviews",
    "recall_lot",
    "replay",
    "retract",
    "retrieve",
]
