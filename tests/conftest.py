"""Test fixtures.

Every test in this suite runs against a REAL CockroachDB cluster. There are no
database mocks: the behaviour under test (a computed column gating a vector
index, a serializable cascade, an AS OF SYSTEM TIME snapshot read) only exists in
CockroachDB, so mocking it would certify nothing.

If RESCIND_DATABASE_URL is unset the whole suite skips rather than pretending to
pass.
"""

from __future__ import annotations

import math
import os

import pytest

from rescind.config import EMBED_DIM
from rescind.db import ENV_VAR, connect

TEST_LOT = "LOT-TEST-0001"

# Tables in foreign-key-safe deletion order.
_TABLES = [
    "decision_support",
    "retractions",
    "decisions",
    "fact_edges",
    "facts",
    "shipments",
    "lots",
]


def pytest_configure(config):
    config.addinivalue_line("markers", "index: asserts query-plan behaviour")


@pytest.fixture(scope="session")
def conn():
    if not os.environ.get(ENV_VAR, "").strip():
        pytest.skip(f"{ENV_VAR} is not set; these tests require a real CockroachDB cluster")
    with connect() as connection:
        missing = [
            t
            for t in _TABLES
            if not connection.execute(
                "SELECT count(*) AS n FROM information_schema.tables "
                "WHERE table_name = %s",
                (t,),
            ).fetchone()["n"]
        ]
        if missing:
            pytest.fail(
                f"schema not applied, missing tables: {missing}. "
                "Run: python scripts/apply_schema.py"
            )
        yield connection


@pytest.fixture(autouse=True)
def clean(conn):
    """Truncate between tests and re-create the lot under test."""
    for table in _TABLES:
        conn.execute(f"DELETE FROM {table}")
    conn.execute(
        """
        INSERT INTO lots (lot_id, product_name, supplier, manufactured_on)
        VALUES (%s, 'Infant Formula, Stage 1, 400g', 'Northvale Dairy Co-op', '2026-06-02')
        """,
        (TEST_LOT,),
    )
    yield


# ---------------------------------------------------------------------------
# Deterministic embeddings with controlled distances.
#
# For unit vectors, L2 distance and cosine are related by L2 = sqrt(2 - 2*cos).
# Building test vectors as an explicit blend of two basis directions lets each
# test state the distance it wants exactly, so threshold assertions are stable
# on every run and on every machine -- no model, no randomness.
# ---------------------------------------------------------------------------


def query_vector() -> list[float]:
    """The reference direction every test measures against."""
    vec = [0.0] * EMBED_DIM
    vec[0] = 1.0
    return vec


def vector_at_cosine(cos: float, axis: int) -> list[float]:
    """A unit vector at exactly `cos` cosine similarity to query_vector().

    `axis` (>=1) keeps distinct vectors distinct from each other.
    """
    if not 0.0 <= cos <= 1.0:
        raise ValueError("cos must be in [0, 1]")
    if axis < 1:
        raise ValueError("axis must be >= 1 to stay orthogonal to the query axis")
    vec = [0.0] * EMBED_DIM
    vec[0] = cos
    vec[axis] = math.sqrt(1.0 - cos * cos)
    return vec


def distance_for_cosine(cos: float) -> float:
    return math.sqrt(2.0 - 2.0 * cos)


# cosine 0.95 -> L2 0.316 (well inside the 0.55 support threshold)
NEAR_COS = 0.95
# cosine 0.20 -> L2 1.265 (well outside it)
FAR_COS = 0.20


def near(axis: int) -> list[float]:
    return vector_at_cosine(NEAR_COS, axis)


def far(axis: int) -> list[float]:
    return vector_at_cosine(FAR_COS, axis)
