"""The agent: answer a question about a lot, and record what it knew when it did.

Every answer writes a decision row plus its exact supporting set, atomically.
That record is what makes retraction meaningful later -- you cannot pull back
conclusions you never wrote down.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

import psycopg

from . import bedrock
from .config import MAX_SUPPORTING_DISTANCE, MIN_SUPPORTING_FACTS, RETRIEVE_LIMIT
from .memory import Recalled, retrieve


@dataclass(frozen=True)
class Decision:
    id: str
    lot_id: str
    question: str
    verdict: str  # release | hold | refused
    rationale: str
    decided_hlc: str
    supporting: list[Recalled]
    model_id: str
    offline: bool

    @property
    def refused(self) -> bool:
        return self.verdict == "refused"


REFUSAL_RATIONALE = (
    "Refused: {found} live supporting record(s) within distance "
    "{threshold} for this lot, but {required} are required. Rescind will not "
    "answer from insufficient memory. Absence of evidence is not evidence of "
    "safety -- this lot is not cleared."
)


def ask(
    conn: psycopg.Connection,
    lot_id: str,
    question: str,
    embedder: Callable[[str], Sequence[float]] | None = None,
    reasoner: Callable[[str, Sequence[str]], dict] | None = None,
    limit: int = RETRIEVE_LIMIT,
) -> Decision:
    """Answer a question about a lot, recording the decision and its support.

    The refusal branch is a deterministic threshold, not a model judgement: if
    fewer than MIN_SUPPORTING_FACTS live facts come back within
    MAX_SUPPORTING_DISTANCE, the agent refuses without ever calling the model.
    It behaves identically on every run, which is what lets CI assert on it and
    what lets a quality director trust it.

    This is also what makes retraction visible from the outside: retract enough
    memory and the same question stops being answerable at all.
    """
    embedder = embedder or bedrock.embed
    reasoner = reasoner or bedrock.reason

    query_vec = embedder(question)
    recalled = retrieve(conn, lot_id, query_vec, limit=limit)
    supporting = [r for r in recalled if r.distance <= MAX_SUPPORTING_DISTANCE]

    if len(supporting) < MIN_SUPPORTING_FACTS:
        verdict = "refused"
        rationale = REFUSAL_RATIONALE.format(
            found=len(supporting),
            threshold=MAX_SUPPORTING_DISTANCE,
            required=MIN_SUPPORTING_FACTS,
        )
        model_id = "none-refused-before-model-call"
        offline = False
    else:
        result = reasoner(question, [r.claim for r in supporting])
        verdict = result["verdict"]
        rationale = result["rationale"]
        model_id = result.get("model_id", "unknown")
        offline = bool(result.get("offline", False))

    decision_id, hlc = _record(
        conn,
        lot_id=lot_id,
        question=question,
        verdict=verdict,
        rationale=rationale,
        supporting=supporting,
        model_id=model_id,
        offline=offline,
    )

    return Decision(
        id=decision_id,
        lot_id=lot_id,
        question=question,
        verdict=verdict,
        rationale=rationale,
        decided_hlc=hlc,
        supporting=supporting,
        model_id=model_id,
        offline=offline,
    )


def _record(
    conn: psycopg.Connection,
    *,
    lot_id: str,
    question: str,
    verdict: str,
    rationale: str,
    supporting: Sequence[Recalled],
    model_id: str,
    offline: bool,
) -> tuple[str, str]:
    """Write the decision and its supporting set in one transaction.

    decided_hlc is cluster_logical_timestamp(), captured by the database at
    commit -- not a wall clock read in Python. That is what makes AS OF SYSTEM
    TIME replay of this decision exact rather than approximate.

    A decision without its supporting set would be an unfalsifiable claim, so the
    two are never written separately.
    """
    with conn.transaction():
        row = conn.execute(
            """
            INSERT INTO decisions (
                lot_id, question, verdict, rationale, decided_hlc, model_id,
                offline_mode
            )
            VALUES (%s, %s, %s, %s, cluster_logical_timestamp(), %s, %s)
            RETURNING id, decided_hlc
            """,
            (lot_id, question, verdict, rationale, model_id, offline),
        ).fetchone()

        if supporting:
            conn.executemany(
                """
                INSERT INTO decision_support (decision_id, fact_id, distance)
                VALUES (%s, %s, %s)
                """,
                [(row["id"], r.id, r.distance) for r in supporting],
            )

    return str(row["id"]), str(row["decided_hlc"])


def open_reviews(conn: psycopg.Connection, lot_id: str | None = None) -> list[dict]:
    """Decisions flagged by a retraction and not yet cleared by a human.

    This is the queue a recall coordinator actually works from.
    """
    sql = """
        SELECT id, lot_id, question, verdict, rationale, review_reason, decided_at
        FROM decisions
        WHERE needs_review = true
    """
    params: tuple = ()
    if lot_id:
        sql += " AND lot_id = %s"
        params = (lot_id,)
    sql += " ORDER BY decided_at"
    return [dict(r, id=str(r["id"])) for r in conn.execute(sql, params).fetchall()]
