"""The behaviour that is the submission.

Each test states what it certifies in its docstring. Read them as the spec.
"""

from __future__ import annotations

import psycopg
import pytest

from conftest import TEST_LOT, far, near, query_vector
from rescind import agent, memory
from rescind.config import MAX_SUPPORTING_DISTANCE, MIN_SUPPORTING_FACTS


def _reasoner_release(question, supporting):
    return {
        "verdict": "release",
        "rationale": "Test reasoner: all supporting records pass.",
        "model_id": "test-stub",
        "offline": True,
    }


def _reasoner_never_called(question, supporting):
    raise AssertionError(
        "the reasoning model was called even though support was below threshold"
    )


def _embedder(_question):
    return query_vector()


# ---------------------------------------------------------------------------
# Provenance is mandatory at write time
# ---------------------------------------------------------------------------


def test_assert_fact_rejects_empty_provenance(conn):
    """An unattributed memory cannot be retracted safely, so it is never stored."""
    with pytest.raises(ValueError, match="provenance is mandatory"):
        memory.assert_fact(conn, TEST_LOT, "Lot is fine.", "   ", near(1))


def test_database_rejects_empty_provenance_too(conn):
    """Provenance is enforced in the database, not only in Python.

    A second writer that bypasses this library still cannot create an
    unattributable memory.
    """
    from rescind.db import to_vector

    with pytest.raises(psycopg.errors.CheckViolation):
        conn.execute(
            """
            INSERT INTO facts (lot_id, kind, claim, source, embedding, asserted_hlc)
            VALUES (%s, 'observation', 'Lot is fine.', '', %s::VECTOR(1024),
                    cluster_logical_timestamp())
            """,
            (TEST_LOT, to_vector(near(1))),
        )


def test_derive_fact_rejects_missing_lineage(conn):
    """A derived fact with no parents is precisely what makes retraction impossible."""
    with pytest.raises(ValueError, match="at least one parent"):
        memory.derive_fact(conn, TEST_LOT, "Lot is releasable.", "agent", near(1), [])


# ---------------------------------------------------------------------------
# Retracted memory is unreachable, not filtered
# ---------------------------------------------------------------------------


def test_retracted_fact_is_unreachable_by_retrieval(conn):
    """After retraction the fact is gone from semantic recall entirely.

    Certifies the round trip: visible before, invisible after, via the same
    retrieval call.
    """
    fact_id = memory.assert_fact(
        conn, TEST_LOT, "Certificate of analysis passed.", "CoA #4471", near(1)
    )

    before = memory.retrieve(conn, TEST_LOT, query_vector())
    assert [r.id for r in before] == [fact_id]

    memory.retract(conn, TEST_LOT, [fact_id], "Supplier withdrew the CoA.")

    after = memory.retrieve(conn, TEST_LOT, query_vector())
    assert after == []


def test_retraction_cascades_through_lineage(conn):
    """Retracting a root pulls down every conclusion transitively built on it.

    Certifies the WITH RECURSIVE walk over fact_edges: root -> derived ->
    derived-of-derived all come down from a single retraction of the root.
    """
    root = memory.assert_fact(
        conn, TEST_LOT, "Supplier audit closed with no findings.", "Audit #22", near(1)
    )
    child = memory.derive_fact(
        conn, TEST_LOT, "Supplier is in good standing.", "agent", near(2), [root]
    )
    grandchild = memory.derive_fact(
        conn, TEST_LOT, "Lot inherits supplier good standing.", "agent", near(3), [child]
    )
    unrelated = memory.assert_fact(
        conn, TEST_LOT, "Cold chain log within range.", "Sensor #9", near(4)
    )

    receipt = memory.retract(conn, TEST_LOT, [root], "Audit finding reopened.")

    assert set(receipt.retracted_fact_ids) == {root, child, grandchild}
    assert unrelated not in receipt.retracted_fact_ids
    assert receipt.cascade_depth_beyond_roots == 2

    surviving = {r.id for r in memory.retrieve(conn, TEST_LOT, query_vector())}
    assert surviving == {unrelated}


# ---------------------------------------------------------------------------
# Decisions are flagged, never silently reversed
# ---------------------------------------------------------------------------


def test_retraction_flags_decisions_without_reversing_them(conn):
    """A retraction flags dependent decisions for review and leaves the verdict alone.

    Reversing a shipment release is a human's call. Certifies that needs_review
    flips, that the audit row names the decision, and that the recorded verdict is
    untouched.
    """
    a = memory.assert_fact(conn, TEST_LOT, "CoA passed.", "CoA #4471", near(1))
    b = memory.assert_fact(conn, TEST_LOT, "Cold chain in range.", "Sensor #9", near(2))

    decision = agent.ask(
        conn, TEST_LOT, "May we release this lot?", _embedder, _reasoner_release
    )
    assert decision.verdict == "release"

    receipt = memory.retract(conn, TEST_LOT, [a], "Lot recalled by supplier.")

    assert receipt.flagged_decision_ids == [decision.id]

    row = conn.execute(
        "SELECT verdict, needs_review, review_reason FROM decisions WHERE id = %s::UUID",
        (decision.id,),
    ).fetchone()
    assert row["verdict"] == "release", "the agent must not silently reverse a decision"
    assert row["needs_review"] is True
    assert "Lot recalled by supplier." in row["review_reason"]

    assert [d["id"] for d in agent.open_reviews(conn, TEST_LOT)] == [decision.id]


def test_retraction_is_all_or_nothing(conn):
    """The cascade, the flagging and the audit row commit together or not at all.

    Certifies that retract()'s writes are a single atomic unit: rolling back the
    enclosing transaction leaves no retracted fact, no flagged decision and no
    audit row behind. A partial retraction is worse than none.
    """
    root = memory.assert_fact(conn, TEST_LOT, "CoA passed.", "CoA #4471", near(1))
    memory.assert_fact(conn, TEST_LOT, "Cold chain in range.", "Sensor #9", near(2))
    decision = agent.ask(
        conn, TEST_LOT, "May we release this lot?", _embedder, _reasoner_release
    )

    class Boom(RuntimeError):
        pass

    with pytest.raises(Boom):
        with conn.transaction():
            memory.retract(conn, TEST_LOT, [root], "Lot recalled by supplier.")
            raise Boom("failure after the retraction, before commit")

    assert conn.execute(
        "SELECT count(*) AS n FROM facts WHERE retracted = true"
    ).fetchone()["n"] == 0
    assert conn.execute(
        "SELECT count(*) AS n FROM decisions WHERE needs_review = true"
    ).fetchone()["n"] == 0
    assert conn.execute("SELECT count(*) AS n FROM retractions").fetchone()["n"] == 0

    assert conn.execute(
        "SELECT needs_review FROM decisions WHERE id = %s::UUID", (decision.id,)
    ).fetchone()["needs_review"] is False


def test_retraction_writes_an_audit_row(conn):
    """Every retraction leaves a durable record of its own blast radius."""
    root = memory.assert_fact(conn, TEST_LOT, "CoA passed.", "CoA #4471", near(1))
    child = memory.derive_fact(
        conn, TEST_LOT, "Lot is releasable.", "agent", near(2), [root]
    )

    receipt = memory.retract(
        conn, TEST_LOT, [root], "FDA Class II recall notice.", actor="d.radrigan"
    )

    row = conn.execute(
        "SELECT actor, reason, facts_retracted, decisions_flagged, "
        "retracted_fact_ids FROM retractions WHERE id = %s::UUID", (receipt.retraction_id,)
    ).fetchone()
    assert row["facts_retracted"] == 2
    assert row["actor"] == "d.radrigan"
    assert row["reason"] == "FDA Class II recall notice."
    assert {str(x) for x in row["retracted_fact_ids"]} == {root, child}


# ---------------------------------------------------------------------------
# The refusal is a deterministic threshold, not a model judgement
# ---------------------------------------------------------------------------


def test_agent_refuses_below_threshold_without_calling_the_model(conn):
    """Below MIN_SUPPORTING_FACTS the agent refuses before the model is ever called.

    Certifies both the refusal and that it is decided by the threshold, not by
    the model: the reasoner raises if invoked.
    """
    memory.assert_fact(conn, TEST_LOT, "CoA passed.", "CoA #4471", near(1))
    memory.assert_fact(conn, TEST_LOT, "Unrelated paperwork.", "Misc", far(2))

    decision = agent.ask(
        conn, TEST_LOT, "May we release this lot?", _embedder, _reasoner_never_called
    )

    assert decision.verdict == "refused"
    assert decision.refused
    assert len(decision.supporting) < MIN_SUPPORTING_FACTS
    assert "not evidence of safety" in decision.rationale


def test_retraction_makes_a_previously_answerable_question_unanswerable(conn):
    """The end-to-end claim, in one test.

    The agent answers a question; a recall retracts one supporting memory; the
    identical question is now refused, because live support fell below threshold.
    Certifies that retraction changes what the agent can conclude, not merely
    what a query returns.
    """
    a = memory.assert_fact(conn, TEST_LOT, "CoA passed.", "CoA #4471", near(1))
    memory.assert_fact(conn, TEST_LOT, "Cold chain in range.", "Sensor #9", near(2))

    first = agent.ask(
        conn, TEST_LOT, "May we release this lot?", _embedder, _reasoner_release
    )
    assert first.verdict == "release"
    assert len(first.supporting) == 2

    memory.retract(conn, TEST_LOT, [a], "Lot recalled: Cronobacter risk.")

    second = agent.ask(
        conn, TEST_LOT, "May we release this lot?", _embedder, _reasoner_never_called
    )
    assert second.verdict == "refused"


def test_refusal_is_deterministic(conn):
    """Identical inputs produce an identical refusal every time.

    The threshold must not drift between runs, or CI cannot assert on it and a
    quality director cannot rely on it.
    """
    memory.assert_fact(conn, TEST_LOT, "CoA passed.", "CoA #4471", near(1))

    verdicts = {
        agent.ask(
            conn, TEST_LOT, "May we release this lot?", _embedder, _reasoner_never_called
        ).verdict
        for _ in range(3)
    }
    assert verdicts == {"refused"}


def test_support_threshold_boundary_is_exact(conn):
    """Facts are counted as support strictly by MAX_SUPPORTING_DISTANCE."""
    from conftest import distance_for_cosine, vector_at_cosine

    inside = 0.96
    outside = 0.80
    assert distance_for_cosine(inside) < MAX_SUPPORTING_DISTANCE
    assert distance_for_cosine(outside) > MAX_SUPPORTING_DISTANCE

    memory.assert_fact(conn, TEST_LOT, "Inside.", "src", vector_at_cosine(inside, 1))
    memory.assert_fact(conn, TEST_LOT, "Outside.", "src", vector_at_cosine(outside, 2))

    recalled = memory.retrieve(conn, TEST_LOT, query_vector())
    assert [r.supports for r in recalled] == [True, False]


# ---------------------------------------------------------------------------
# Replay is exact, not reconstructed
# ---------------------------------------------------------------------------


def test_replay_reads_the_snapshot_the_agent_actually_read(conn):
    """AS OF SYSTEM TIME <decided_hlc> returns the memory state at decision time.

    Certifies the before/after proof: the same query, with the same
    `retracted = false` filter, returns the supporting facts when run against the
    decision's HLC snapshot and returns fewer of them when run against the
    present.
    """
    a = memory.assert_fact(conn, TEST_LOT, "CoA passed.", "CoA #4471", near(1))
    memory.assert_fact(conn, TEST_LOT, "Cold chain in range.", "Sensor #9", near(2))

    decision = agent.ask(
        conn, TEST_LOT, "May we release this lot?", _embedder, _reasoner_release
    )

    memory.retract(conn, TEST_LOT, [a], "Lot recalled: Cronobacter risk.")

    report = memory.replay(conn, decision.id)

    assert len(report.facts_then) == 2, "both facts were live when the agent decided"
    assert len(report.facts_now) == 1, "one has since been retracted"
    assert [f["id"] for f in report.withdrawn_since] == [a]
    assert report.needs_review is True
    assert report.verdict == "release"
    assert report.decided_hlc == decision.decided_hlc
