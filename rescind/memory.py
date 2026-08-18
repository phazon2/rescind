"""Retractable agent memory on CockroachDB.

Five operations: assert_fact, derive_fact, retrieve, retract, replay.

The interesting one is retract(). Everything else exists to make retract()
possible and provable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence

import psycopg

from .config import MAX_SUPPORTING_DISTANCE, RETRIEVE_LIMIT
from .db import safe_hlc, to_vector
from .retry import with_retry

VECTOR_CAST = "%s::VECTOR(1024)"


# ---------------------------------------------------------------------------
# Return types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Recalled:
    """A fact returned by semantic retrieval, with the distance it came back at."""

    id: str
    kind: str
    claim: str
    source: str
    distance: float

    @property
    def supports(self) -> bool:
        return self.distance <= MAX_SUPPORTING_DISTANCE


@dataclass(frozen=True)
class RetractionReceipt:
    """The blast radius of one retraction, as committed to the audit table."""

    retraction_id: str
    lot_id: str
    reason: str
    actor: str
    root_fact_ids: list[str]
    retracted_fact_ids: list[str]
    flagged_decision_ids: list[str]
    retracted_hlc: str

    @property
    def facts_retracted(self) -> int:
        return len(self.retracted_fact_ids)

    @property
    def decisions_flagged(self) -> int:
        return len(self.flagged_decision_ids)

    @property
    def cascade_depth_beyond_roots(self) -> int:
        return len(set(self.retracted_fact_ids) - set(self.root_fact_ids))


@dataclass(frozen=True)
class ReplayReport:
    """What the agent knew then, what it knows now, and the difference."""

    decision_id: str
    question: str
    verdict: str
    rationale: str
    decided_hlc: str
    needs_review: bool
    review_reason: str | None
    facts_then: list[dict[str, Any]] = field(default_factory=list)
    facts_now: list[dict[str, Any]] = field(default_factory=list)

    @property
    def withdrawn_since(self) -> list[dict[str, Any]]:
        live_now = {f["id"] for f in self.facts_now}
        return [f for f in self.facts_then if f["id"] not in live_now]


# ---------------------------------------------------------------------------
# Writing memory
# ---------------------------------------------------------------------------


def _require_provenance(source: str) -> str:
    """An unattributed memory cannot be retracted safely, so it is never stored."""
    cleaned = (source or "").strip()
    if not cleaned:
        raise ValueError(
            "provenance is mandatory: assert_fact requires a non-empty source"
        )
    return cleaned


def assert_fact(
    conn: psycopg.Connection,
    lot_id: str,
    claim: str,
    source: str,
    embedding: Sequence[float],
    kind: str = "observation",
) -> str:
    """Record a first-hand observation about a lot. Returns the fact id."""
    source = _require_provenance(source)
    if not (claim or "").strip():
        raise ValueError("claim must not be empty")

    row = conn.execute(
        f"""
        INSERT INTO facts (lot_id, kind, claim, source, embedding, asserted_hlc)
        VALUES (%s, %s, %s, %s, {VECTOR_CAST}, cluster_logical_timestamp())
        RETURNING id
        """,
        (lot_id, kind, claim.strip(), source, to_vector(embedding)),
    ).fetchone()
    return str(row["id"])


def derive_fact(
    conn: psycopg.Connection,
    lot_id: str,
    claim: str,
    source: str,
    embedding: Sequence[float],
    parents: Sequence[str],
) -> str:
    """Record a conclusion built on other facts, with its lineage.

    Rejects an empty parent list. A derived memory with no recorded parents is
    exactly the thing that makes retraction impossible in every other store, so
    we refuse to create one.
    """
    source = _require_provenance(source)
    parent_ids = [str(p) for p in (parents or [])]
    if not parent_ids:
        raise ValueError(
            "derive_fact requires at least one parent: a derived fact without "
            "lineage cannot be retracted safely"
        )

    # The fact and its lineage land together or not at all.
    with conn.transaction():
        fact_id = assert_fact(
            conn, lot_id, claim, source, embedding, kind="derived"
        )
        # executemany lives on the cursor, not the connection.
        # Explicit ::UUID casts: psycopg sends Python strings as text, and a text
        # parameter is not implicitly assignable to a UUID column.
        with conn.cursor() as cur:
            cur.executemany(
                "INSERT INTO fact_edges (parent_id, child_id) VALUES (%s::UUID, %s::UUID)",
                [(pid, fact_id) for pid in dict.fromkeys(parent_ids)],
            )
    return fact_id


# ---------------------------------------------------------------------------
# Reading memory
# ---------------------------------------------------------------------------


def retrieve(
    conn: psycopg.Connection,
    lot_id: str,
    query_embedding: Sequence[float],
    limit: int = RETRIEVE_LIMIT,
) -> list[Recalled]:
    """Semantic recall over LIVE memory for one lot.

    Note `retracted = false`. It is not an optimisation and it is not defensive
    application-level filtering: `retracted` is a prefix column of the vector
    index facts_live_by_lot, and CockroachDB will not use a vector index unless
    every prefix column is equality-constrained. The query shape is therefore
    forced to declare it. Retracted memory is not reachable from here.
    """
    vec = to_vector(query_embedding)
    rows = conn.execute(
        f"""
        SELECT id, kind, claim, source,
               embedding <-> {VECTOR_CAST} AS distance
        FROM facts
        WHERE lot_id = %s AND retracted = false
        ORDER BY embedding <-> {VECTOR_CAST}
        LIMIT %s
        """,
        (vec, lot_id, vec, limit),
    ).fetchall()

    return [
        Recalled(
            id=str(r["id"]),
            kind=r["kind"],
            claim=r["claim"],
            source=r["source"],
            distance=float(r["distance"]),
        )
        for r in rows
    ]


def explain_retrieval(
    conn: psycopg.Connection, lot_id: str, query_embedding: Sequence[float]
) -> str:
    """Return the query plan for a retrieval.

    Used by the test suite and by scripts/probe_cockroach.py to prove the vector
    index is actually being used, rather than asserting it in prose.
    """
    vec = to_vector(query_embedding)
    rows = conn.execute(
        f"""
        EXPLAIN SELECT id, claim FROM facts
        WHERE lot_id = %s AND retracted = false
        ORDER BY embedding <-> {VECTOR_CAST}
        LIMIT 5
        """,
        (lot_id, vec),
    ).fetchall()
    return "\n".join(str(list(r.values())[0]) for r in rows)


# ---------------------------------------------------------------------------
# Retraction: the whole point
# ---------------------------------------------------------------------------

def retract(
    conn: psycopg.Connection,
    lot_id: str,
    root_fact_ids: Sequence[str],
    reason: str,
    actor: str = "recall-coordinator",
) -> RetractionReceipt:
    """Withdraw facts and everything derived from them, in ONE transaction.

    Four statements, one serializable transaction:

      1. walk fact_edges to the full transitive descendant set;
      2. mark every one of them retracted (which flips the computed `retracted`
         column, which removes them from the vector index prefix -- they become
         unreachable by retrieval);
      3. flag every standing decision resting on any of them as needs_review;
      4. write the audit row recording the blast radius.

    All four commit together or not at all. A partial retraction is worse than
    none: it leaves conclusions standing on facts the system has already
    disowned.

    Decisions are FLAGGED, never silently reversed. Reversing a shipment release
    is a human's call, and a system that made it automatically would be its own
    kind of untrustworthy.
    """
    roots = [str(r) for r in (root_fact_ids or [])]
    if not roots:
        raise ValueError("retract requires at least one root fact id")
    if not (reason or "").strip():
        raise ValueError("retract requires a non-empty reason (this is an audit record)")
    reason = reason.strip()

    # CockroachDB is SERIALIZABLE with optimistic concurrency, so this
    # transaction can be aborted with SQLSTATE 40001 and must be retried by the
    # client. A recall that gave up because another writer touched the same lot
    # would leave conclusions standing on disowned facts.
    return with_retry(conn, lambda: _retract_once(conn, lot_id, roots, reason, actor))


def _retract_once(
    conn: psycopg.Connection,
    lot_id: str,
    roots: list[str],
    reason: str,
    actor: str,
) -> RetractionReceipt:
    """One attempt at the retraction transaction. Safe to replay from the start.

    The cascade runs entirely server-side. An earlier version walked the lineage
    with a SELECT, pulled every descendant id back into Python, and sent them
    home again inside `id = ANY($1)`. Benchmarking showed that transaction was
    slow enough at depth to have its read timestamp pushed and fail the refresh,
    so it exhausted its retry budget instead of committing. Driving the UPDATE
    directly from the recursive CTE keeps the whole closure inside the database
    and cuts the transaction's lifetime, which is exactly what the
    `designing-application-transactions` skill prescribes -- push invariants into
    SQL, prefer set-based operations.

    This shape still has a ceiling: one transaction covers one bounded closure.
    scripts/benchmark_scale.py sweeps until it breaks and ci/scale.json records
    where, so the limit is measured and published rather than left to be
    discovered in production. See docs/LIMITS.md.
    """
    with conn.transaction():
        # A recall is the highest-value write in the system: if it contends with
        # ordinary agent writes it should win rather than be aborted and retried.
        conn.execute("SET TRANSACTION PRIORITY HIGH")

        # 1 + 2. Walk the lineage and retract the whole closure, in one statement.
        #        Only rows not already retracted are touched, so a replayed recall
        #        is idempotent rather than rewriting history.
        newly_retracted = [
            str(r["id"])
            for r in conn.execute(
                """
                WITH RECURSIVE descendants (id) AS (
                    SELECT unnest(%s::UUID[])
                  UNION
                    SELECT e.child_id
                    FROM fact_edges AS e
                    JOIN descendants AS d ON e.parent_id = d.id
                )
                UPDATE facts
                   SET retracted_at = now(), retracted_reason = %s
                 WHERE id IN (SELECT id FROM descendants)
                   AND retracted_at IS NULL
             RETURNING id
                """,
                (roots, reason),
            ).fetchall()
        ]

        # 3. Flag -- never reverse -- every decision resting on a retracted fact.
        #    The closure is recomputed server-side rather than shipped back in,
        #    which keeps the transaction short.
        flagged = [
            str(r["id"])
            for r in conn.execute(
                """
                WITH RECURSIVE descendants (id) AS (
                    SELECT unnest(%s::UUID[])
                  UNION
                    SELECT e.child_id
                    FROM fact_edges AS e
                    JOIN descendants AS d ON e.parent_id = d.id
                )
                UPDATE decisions
                   SET needs_review = true, review_reason = %s
                 WHERE id IN (
                           SELECT s.decision_id
                             FROM decision_support AS s
                            WHERE s.fact_id IN (SELECT id FROM descendants)
                       )
                   AND needs_review = false
             RETURNING id
                """,
                (roots, f"supporting memory retracted: {reason}"),
            ).fetchall()
        ]

        # 4. Audit row, same transaction as the damage it describes.
        receipt = conn.execute(
            """
            INSERT INTO retractions (
                lot_id, reason, actor, root_fact_ids, retracted_fact_ids,
                flagged_decision_ids, facts_retracted, decisions_flagged,
                retracted_hlc
            )
            VALUES (%s, %s, %s, %s::UUID[], %s::UUID[], %s::UUID[], %s, %s,
                    cluster_logical_timestamp())
            RETURNING id, retracted_hlc
            """,
            (
                lot_id,
                reason,
                actor,
                roots,
                newly_retracted,
                flagged,
                len(newly_retracted),
                len(flagged),
            ),
        ).fetchone()

    return RetractionReceipt(
        retraction_id=str(receipt["id"]),
        lot_id=lot_id,
        reason=reason,
        actor=actor,
        root_fact_ids=roots,
        retracted_fact_ids=newly_retracted,
        flagged_decision_ids=flagged,
        retracted_hlc=str(receipt["retracted_hlc"]),
    )


def recall_lot(
    conn: psycopg.Connection,
    lot_id: str,
    reason: str,
    actor: str = "recall-coordinator",
) -> RetractionReceipt:
    """Recall a physical lot: mark the lot recalled and retract its root memory.

    This is the operation a recall coordinator actually performs. Root facts are
    the lot's first-hand observations; everything derived from them comes down by
    cascade.
    """
    with conn.transaction():
        conn.execute(
            "UPDATE lots SET status = 'recalled', recalled_at = now() WHERE lot_id = %s",
            (lot_id,),
        )
        roots = [
            str(r["id"])
            for r in conn.execute(
                """
                SELECT id FROM facts
                 WHERE lot_id = %s AND kind = 'observation' AND retracted_at IS NULL
                """,
                (lot_id,),
            ).fetchall()
        ]
        if not roots:
            raise ValueError(f"no live observations to retract for lot {lot_id}")
        return retract(conn, lot_id, roots, reason, actor)


# ---------------------------------------------------------------------------
# Replay: exact, not reconstructed
# ---------------------------------------------------------------------------

# The SAME query is run twice -- once against the historical snapshot, once
# against the present. Identical text, identical `retracted = false` filter. The
# only difference is which MVCC snapshot it reads. That is the proof: we are not
# reconstructing what the agent knew, we are re-reading it.
_SUPPORT_SQL = """
SELECT f.id, f.claim, f.source, f.kind, s.distance
FROM decision_support AS s
JOIN facts AS f ON f.id = s.fact_id
WHERE s.decision_id = %s::UUID AND f.retracted = false
ORDER BY s.distance
"""


def _rows_as_of(
    conn: psycopg.Connection, hlc: str, sql: str, params: tuple
) -> list[dict[str, Any]]:
    """Run a query inside a snapshot transaction pinned to an exact HLC.

    `SET TRANSACTION AS OF SYSTEM TIME` must be the first statement in the
    transaction. Using a transaction rather than an inline AS OF SYSTEM TIME
    clause keeps the query text byte-identical to the present-time query.
    """
    conn.execute("BEGIN")
    try:
        conn.execute(f"SET TRANSACTION AS OF SYSTEM TIME {hlc}")
        rows = conn.execute(sql, params).fetchall()
        conn.execute("COMMIT")
        return rows
    except Exception:
        conn.execute("ROLLBACK")
        raise


def replay(conn: psycopg.Connection, decision_id: str) -> ReplayReport:
    """Reconstruct the exact memory state a decision was made on.

    decisions.decided_hlc holds cluster_logical_timestamp() -- a hybrid logical
    clock reading, not a wall clock. Replaying with AS OF SYSTEM TIME <hlc>
    therefore reads the IDENTICAL MVCC snapshot the agent read, not an
    approximation of it. Wall-clock replay can straddle concurrent writes; this
    cannot.
    """
    decision = conn.execute(
        """
        SELECT id, question, verdict, rationale, decided_hlc, needs_review,
               review_reason
        FROM decisions WHERE id = %s::UUID
        """,
        (decision_id,),
    ).fetchone()
    if decision is None:
        raise LookupError(f"no such decision: {decision_id}")

    # Validated as a bare decimal literal before it is interpolated into SQL.
    hlc = safe_hlc(decision["decided_hlc"])

    facts_then = _rows_as_of(conn, hlc, _SUPPORT_SQL, (decision_id,))
    facts_now = conn.execute(_SUPPORT_SQL, (decision_id,)).fetchall()

    return ReplayReport(
        decision_id=str(decision["id"]),
        question=decision["question"],
        verdict=decision["verdict"],
        rationale=decision["rationale"],
        decided_hlc=hlc,
        needs_review=bool(decision["needs_review"]),
        review_reason=decision["review_reason"],
        facts_then=[dict(r, id=str(r["id"])) for r in facts_then],
        facts_now=[dict(r, id=str(r["id"])) for r in facts_now],
    )
