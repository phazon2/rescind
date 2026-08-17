#!/usr/bin/env python3
"""Probe the cluster for the CockroachDB behaviours Rescind depends on.

Each probe is a claim the README makes. Running this turns each one from an
assumption into an observation, and writes the result to ci/probe.json so the
repository carries evidence rather than assertion.

Never fails the build: its job is to report, not to gate.
"""

from __future__ import annotations

import json
import os
import pathlib
import sys
import traceback

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from rescind.config import EMBED_DIM  # noqa: E402
from rescind.db import connect  # noqa: E402

RESULTS: list[dict] = []


def probe(name: str, claim: str):
    def decorator(fn):
        def run(conn):
            try:
                detail = fn(conn)
                RESULTS.append(
                    {"probe": name, "claim": claim, "supported": True, "detail": detail}
                )
                print(f"  [ OK ] {name}: {detail}")
            except Exception as exc:  # noqa: BLE001
                RESULTS.append(
                    {
                        "probe": name,
                        "claim": claim,
                        "supported": False,
                        "detail": f"{type(exc).__name__}: {exc}",
                    }
                )
                print(f"  [FAIL] {name}: {type(exc).__name__}: {exc}")

        run.__name__ = fn.__name__
        return run

    return decorator


@probe(
    "vector_index_setting",
    "Vector indexes require SET CLUSTER SETTING feature.vector_index.enabled = true",
)
def p_setting(conn):
    conn.execute("SET CLUSTER SETTING feature.vector_index.enabled = true")
    row = conn.execute(
        "SHOW CLUSTER SETTING feature.vector_index.enabled"
    ).fetchone()
    return f"setting is {list(row.values())[0]}"


@probe(
    "computed_column_as_vector_index_prefix",
    "A STORED computed column can be a prefix column of a vector index",
)
def p_computed_prefix(conn):
    conn.execute("DROP TABLE IF EXISTS probe_computed")
    conn.execute(
        f"""
        CREATE TABLE probe_computed (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            lot_id STRING NOT NULL,
            retracted_at TIMESTAMPTZ,
            retracted BOOL NOT NULL AS (retracted_at IS NOT NULL) STORED,
            embedding VECTOR({EMBED_DIM}) NOT NULL
        )
        """
    )
    conn.execute(
        "CREATE VECTOR INDEX probe_computed_idx "
        "ON probe_computed (lot_id, retracted, embedding)"
    )
    conn.execute("DROP TABLE probe_computed")
    return "accepted"


@probe(
    "recursive_cte_with_update",
    "WITH RECURSIVE can drive an UPDATE in a single statement",
)
def p_recursive_update(conn):
    conn.execute("DROP TABLE IF EXISTS probe_edges")
    conn.execute("CREATE TABLE probe_edges (parent INT, child INT, done BOOL DEFAULT false)")
    conn.execute("INSERT INTO probe_edges (parent, child) VALUES (1, 2), (2, 3)")
    conn.execute(
        """
        WITH RECURSIVE d (id) AS (
            SELECT 1
          UNION
            SELECT e.child FROM probe_edges e JOIN d ON e.parent = d.id
        )
        UPDATE probe_edges SET done = true WHERE child IN (SELECT id FROM d)
        """
    )
    conn.execute("DROP TABLE probe_edges")
    return "single-statement form parses"


@probe(
    "hlc_and_time_travel",
    "cluster_logical_timestamp() can pin AS OF SYSTEM TIME to an exact snapshot",
)
def p_time_travel(conn):
    hlc = str(
        list(conn.execute("SELECT cluster_logical_timestamp() AS t").fetchone().values())[0]
    )
    conn.execute("BEGIN")
    try:
        conn.execute(f"SET TRANSACTION AS OF SYSTEM TIME {hlc}")
        conn.execute("SELECT count(*) FROM lots")
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
    return f"snapshot read at hlc {hlc}"


@probe(
    "vector_index_used_by_retrieval",
    "The retrieval query plan actually uses facts_live_by_lot",
)
def p_index_used(conn):
    from rescind.memory import explain_retrieval

    plan = explain_retrieval(conn, "LOT-PROBE", [0.0] * (EMBED_DIM - 1) + [1.0])
    used = "facts_live_by_lot" in plan
    if not used:
        raise AssertionError(
            "plan does not name facts_live_by_lot (may be a small-table scan): "
            + " ".join(plan.split())[:200]
        )
    return "plan uses facts_live_by_lot"


@probe("titan_embedding_dimensions", f"Titan returns exactly {EMBED_DIM} dimensions")
def p_titan(conn):
    if os.environ.get("RESCIND_OFFLINE", "").lower() in {"1", "true", "yes"}:
        raise AssertionError("skipped: RESCIND_OFFLINE is set, no AWS call attempted")
    from rescind.bedrock import embed

    vector = embed("probe: infant formula lot release check")
    if len(vector) != EMBED_DIM:
        raise AssertionError(f"got {len(vector)} dimensions")
    return f"{len(vector)} dimensions"


PROBES = [p_setting, p_computed_prefix, p_recursive_update, p_time_travel, p_index_used, p_titan]


def main() -> int:
    print("Probing CockroachDB for the behaviours Rescind depends on:\n")
    try:
        with connect() as conn:
            version = list(conn.execute("SELECT version() AS v").fetchone().values())[0]
            print(f"cluster: {version}\n")
            for p in PROBES:
                p(conn)
    except Exception:  # noqa: BLE001
        traceback.print_exc()
        version = "unreachable"

    out = pathlib.Path(__file__).resolve().parent.parent / "ci" / "probe.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({"cluster": version, "probes": RESULTS}, indent=2) + "\n")
    print(f"\nwrote {out.relative_to(out.parent.parent)}")

    supported = sum(1 for r in RESULTS if r["supported"])
    print(f"{supported}/{len(RESULTS)} probes supported")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
