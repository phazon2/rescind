"""Connection handling and the one type conversion CockroachDB needs from us."""

from __future__ import annotations

import os
import re
from contextlib import contextmanager
from typing import Iterator, Sequence

import psycopg
from psycopg.rows import dict_row

from .config import EMBED_DIM

ENV_VAR = "RESCIND_DATABASE_URL"

# cluster_logical_timestamp() returns a DECIMAL like "1755438912345678901.0000000001".
# We interpolate HLCs into AS OF SYSTEM TIME clauses (they cannot always be
# passed as placeholders), so every HLC is validated against this pattern first.
# Anything that is not a bare decimal literal is rejected before it reaches SQL.
_HLC_RE = re.compile(r"\A\d{1,30}(\.\d{1,30})?\Z")


class ConfigError(RuntimeError):
    pass


def dsn() -> str:
    url = os.environ.get(ENV_VAR, "").strip()
    if not url:
        raise ConfigError(
            f"{ENV_VAR} is not set. Point it at a CockroachDB cluster, e.g.\n"
            f"  export {ENV_VAR}='postgresql://root@localhost:26257/rescind?sslmode=disable'"
        )
    return url


@contextmanager
def connect(autocommit: bool = True) -> Iterator[psycopg.Connection]:
    """Open a connection with dict rows.

    CockroachDB runs SERIALIZABLE isolation by default, which is what the
    retraction transaction relies on -- we do not weaken it anywhere.
    """
    conn = psycopg.connect(dsn(), row_factory=dict_row, autocommit=autocommit)
    try:
        yield conn
    finally:
        conn.close()


def to_vector(values: Sequence[float]) -> str:
    """Render a Python sequence as a CockroachDB VECTOR literal.

    Always cast the resulting parameter explicitly in SQL (``%s::VECTOR(1024)``).
    """
    if len(values) != EMBED_DIM:
        raise ValueError(
            f"embedding must have exactly {EMBED_DIM} dimensions, got {len(values)}"
        )
    return "[" + ",".join(repr(float(v)) for v in values) + "]"


def safe_hlc(hlc: object) -> str:
    """Validate an HLC so it can be safely interpolated into AS OF SYSTEM TIME."""
    text = str(hlc).strip()
    if not _HLC_RE.match(text):
        raise ValueError(f"refusing to interpolate non-decimal HLC: {text!r}")
    return text
