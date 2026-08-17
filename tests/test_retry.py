"""Retry behaviour for serialization failures.

These tests exist because auditing Rescind against the CockroachDB Agent Skills
repo (the `designing-application-transactions` skill) surfaced that the
retraction transaction had no client-side retry, which SERIALIZABLE isolation
requires.
"""

from __future__ import annotations

import psycopg
import pytest

from rescind import memory
from rescind.retry import RetryExhausted, in_transaction, is_serialization_failure, with_retry
from conftest import TEST_LOT, near


class _Serialization(psycopg.errors.SerializationFailure):
    pass


def _failing_times(n: int):
    """An operation that raises 40001 `n` times, then succeeds."""
    state = {"calls": 0}

    def op():
        state["calls"] += 1
        if state["calls"] <= n:
            raise _Serialization("restart transaction: TransactionRetryError")
        return "committed"

    return op, state


def test_recognises_serialization_failures():
    """40001 is retryable; nothing else is."""
    assert is_serialization_failure(_Serialization("boom"))
    assert not is_serialization_failure(ValueError("boom"))


def test_retries_until_it_commits(conn):
    """A transaction aborted by contention is replayed, not abandoned.

    A recall that gave up because another writer touched the same lot would
    leave conclusions standing on facts the system has already disowned.
    """
    op, state = _failing_times(3)
    slept: list[float] = []

    result = with_retry(conn, op, sleep=slept.append)

    assert result == "committed"
    assert state["calls"] == 4
    assert slept == [0.05, 0.1, 0.2], "delays must back off exponentially"


def test_gives_up_loudly_rather_than_reporting_false_success(conn):
    """Exhausting the retry budget raises. It never returns a partial result."""
    op, state = _failing_times(99)

    with pytest.raises(RetryExhausted, match="NOT applied"):
        with_retry(conn, op, max_attempts=3, sleep=lambda _: None)

    assert state["calls"] == 3


def test_non_retryable_errors_propagate_immediately(conn):
    """A logic error must not be retried five times and then reported as contention."""
    calls = {"n": 0}

    def op():
        calls["n"] += 1
        raise ValueError("a real bug")

    with pytest.raises(ValueError, match="a real bug"):
        with_retry(conn, op, sleep=lambda _: None)

    assert calls["n"] == 1


def test_defers_to_an_enclosing_transaction(conn):
    """Inside a caller's transaction, the caller owns the retry.

    Retrying an inner savepoint would replay against the outer transaction's
    stale snapshot and could silently produce a wrong result, so 40001 is allowed
    to propagate instead.
    """
    op, state = _failing_times(1)

    assert not in_transaction(conn)
    with pytest.raises(psycopg.errors.SerializationFailure):
        with conn.transaction():
            assert in_transaction(conn)
            with_retry(conn, op, sleep=lambda _: None)

    assert state["calls"] == 1, "must not retry inside an enclosing transaction"


def test_retraction_still_commits_normally(conn):
    """The retry wrapper does not change retract()'s behaviour in the happy path."""
    root = memory.assert_fact(conn, TEST_LOT, "CoA passed.", "CoA #4471", near(1))
    child = memory.derive_fact(
        conn, TEST_LOT, "Lot is releasable.", "agent", near(2), [root]
    )

    receipt = memory.retract(conn, TEST_LOT, [root], "Recalled.")

    assert set(receipt.retracted_fact_ids) == {root, child}
