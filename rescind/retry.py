"""Client-side retry for serialization failures.

WHY THIS EXISTS: this module was written after auditing Rescind against the
CockroachDB Agent Skills repo (cockroachlabs/cockroachdb-skills), specifically
the `designing-application-transactions` skill. That skill's guidance on retry
handling identified a real gap: CockroachDB runs SERIALIZABLE isolation and uses
optimistic concurrency, so any transaction can be aborted with SQLSTATE 40001
and MUST be retried by the client. Rescind's retraction transaction had no such
handling, which meant that under concurrent writes to the same lot a legitimate
recall could simply fail.

That failure mode matters more here than in most applications. A retraction that
gives up because another writer touched the same lot leaves conclusions standing
on facts the system has already disowned -- which is the exact condition this
project exists to prevent.
"""

from __future__ import annotations

import logging
import time
from typing import Callable, TypeVar

import psycopg

log = logging.getLogger("rescind.retry")

T = TypeVar("T")

# SQLSTATE 40001. CockroachDB raises this when a transaction must be restarted.
SERIALIZATION_FAILURE = "40001"

MAX_ATTEMPTS = 5
BASE_DELAY_SECONDS = 0.05


def is_serialization_failure(exc: BaseException) -> bool:
    return (
        isinstance(exc, psycopg.errors.SerializationFailure)
        or getattr(exc, "sqlstate", None) == SERIALIZATION_FAILURE
    )


def in_transaction(conn: psycopg.Connection) -> bool:
    """True if the connection is already inside an explicit transaction.

    When Rescind's operations are composed inside a caller's transaction, the
    caller owns the retry, not us: retrying an inner savepoint would not re-read
    the outer transaction's stale snapshot and would silently produce a wrong
    result. In that case we let 40001 propagate.
    """
    return conn.info.transaction_status != psycopg.pq.TransactionStatus.IDLE


def with_retry(
    conn: psycopg.Connection,
    operation: Callable[[], T],
    *,
    max_attempts: int = MAX_ATTEMPTS,
    base_delay: float = BASE_DELAY_SECONDS,
    sleep: Callable[[float], None] = time.sleep,
) -> T:
    """Run `operation`, retrying it on serialization failures with backoff.

    `operation` must be idempotent when replayed from the start, because that is
    exactly what a retry does. Rescind's retraction is: it only ever moves facts
    from live to retracted and only flags decisions that are not yet flagged, so
    replaying it converges on the same state.

    Delays are 50ms, 100ms, 200ms, 400ms. Deliberately not jittered: the demo and
    the test suite assert on retry behaviour, and determinism is worth more here
    than the marginal contention benefit of jitter at this scale.
    """
    if in_transaction(conn):
        # The caller owns the transaction, so the caller owns the retry.
        return operation()

    last: BaseException | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            return operation()
        except Exception as exc:  # noqa: BLE001
            if not is_serialization_failure(exc):
                raise
            last = exc
            if attempt == max_attempts:
                break
            delay = base_delay * (2 ** (attempt - 1))
            log.warning(
                "serialization failure (40001) on attempt %d/%d, retrying in %.0fms",
                attempt,
                max_attempts,
                delay * 1000,
            )
            sleep(delay)

    raise RetryExhausted(
        f"transaction still hitting serialization failures after {max_attempts} "
        f"attempts; the operation was NOT applied"
    ) from last


class RetryExhausted(RuntimeError):
    """Raised when a transaction could not be committed within the retry budget.

    Raised rather than returning a partial result: a caller that believes a
    retraction succeeded when it did not is the worst possible outcome here.
    """
