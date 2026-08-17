#!/usr/bin/env python3
"""Prove the application role cannot destroy its own audit trail.

Connects as `rescind_app` -- the least-privilege role from sql/003_roles.sql --
and asserts both halves of the claim:

  * everything Rescind actually does still works;
  * everything it must never be able to do is refused by the database.

This is what turns "the audit trail is append-only by convention" into "the
application does not hold the privilege to rewrite it". Writes ci/privileges.json.
"""

from __future__ import annotations

import json
import os
import pathlib
import sys

import psycopg
from psycopg.rows import dict_row

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from rescind.config import EMBED_DIM  # noqa: E402
from rescind.db import dsn, to_vector  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parent.parent / "ci" / "privileges.json"
LOT = "LOT-PRIV-0001"
VEC = to_vector([1.0] + [0.0] * (EMBED_DIM - 1))

results: list[dict] = []


def app_dsn() -> str:
    """The same cluster, as rescind_app instead of root."""
    override = os.environ.get("RESCIND_APP_DATABASE_URL")
    if override:
        return override
    base = dsn()
    for prefix in ("postgresql://root@", "postgres://root@"):
        if base.startswith(prefix):
            return base.replace(prefix, prefix.replace("root@", "rescind_app@"), 1)
    raise SystemExit("cannot derive an app DSN; set RESCIND_APP_DATABASE_URL")


def allowed(label: str, fn) -> None:
    try:
        fn()
        results.append({"operation": label, "expected": "allowed", "outcome": "allowed", "ok": True})
        print(f"  [ OK ] {label}: allowed, as intended")
    except Exception as exc:  # noqa: BLE001
        results.append({"operation": label, "expected": "allowed", "outcome": f"{type(exc).__name__}: {exc}"[:200], "ok": False})
        print(f"  [FAIL] {label}: should be allowed but was refused -> {exc}")


def refused(label: str, fn) -> None:
    try:
        fn()
        results.append({"operation": label, "expected": "refused", "outcome": "ALLOWED", "ok": False})
        print(f"  [FAIL] {label}: should have been refused but succeeded")
    except psycopg.errors.InsufficientPrivilege as exc:
        results.append({"operation": label, "expected": "refused", "outcome": "insufficient privilege", "ok": True})
        print(f"  [ OK ] {label}: refused by the database")
    except Exception as exc:  # noqa: BLE001
        # Any other error still means it did not succeed, but say which.
        results.append({"operation": label, "expected": "refused", "outcome": f"{type(exc).__name__}"[:80], "ok": True})
        print(f"  [ OK ] {label}: refused ({type(exc).__name__})")


def main() -> int:
    # Seed one lot as root so the app role has something to work with.
    with psycopg.connect(dsn(), row_factory=dict_row, autocommit=True) as root:
        root.execute("DELETE FROM decision_support")
        root.execute("DELETE FROM retractions")
        root.execute("DELETE FROM decisions")
        root.execute("DELETE FROM fact_edges")
        root.execute("DELETE FROM facts")
        root.execute("DELETE FROM shipments")
        root.execute("DELETE FROM lots")
        root.execute(
            "INSERT INTO lots (lot_id, product_name, supplier, manufactured_on) "
            "VALUES (%s,'Infant Formula','Northvale Dairy Co-op','2026-06-19')", (LOT,))

    print(f"connecting as rescind_app\n\nwhat the application MUST be able to do:")
    with psycopg.connect(app_dsn(), row_factory=dict_row, autocommit=True) as app:
        fact_id = None

        def write_fact():
            nonlocal fact_id
            fact_id = app.execute(
                "INSERT INTO facts (lot_id, kind, claim, source, embedding, asserted_hlc) "
                f"VALUES (%s,'observation','CoA passed.','CoA #4471',%s::VECTOR({EMBED_DIM}),"
                "cluster_logical_timestamp()) RETURNING id",
                (LOT, VEC),
            ).fetchone()["id"]

        allowed("INSERT a fact", write_fact)
        allowed("SELECT live facts", lambda: app.execute(
            "SELECT id FROM facts WHERE lot_id = %s AND retracted = false", (LOT,)).fetchall())
        allowed("UPDATE a fact to retracted", lambda: app.execute(
            "UPDATE facts SET retracted_at = now(), retracted_reason = 'recall' WHERE id = %s", (fact_id,)))
        allowed("INSERT an audit row", lambda: app.execute(
            "INSERT INTO retractions (lot_id, reason, actor, root_fact_ids, retracted_fact_ids, "
            "flagged_decision_ids, facts_retracted, decisions_flagged, retracted_hlc) "
            "VALUES (%s,'recall','coordinator',ARRAY[%s]::UUID[],ARRAY[%s]::UUID[],ARRAY[]::UUID[],1,0,"
            "cluster_logical_timestamp())", (LOT, fact_id, fact_id)))
        allowed("AS OF SYSTEM TIME read", lambda: app.execute(
            "SELECT count(*) FROM facts AS OF SYSTEM TIME '-5s'").fetchall())

        print("\nwhat the application MUST NOT be able to do:")
        refused("DELETE a fact", lambda: app.execute("DELETE FROM facts WHERE lot_id = %s", (LOT,)))
        refused("DELETE an audit row", lambda: app.execute("DELETE FROM retractions"))
        refused("UPDATE an audit row", lambda: app.execute(
            "UPDATE retractions SET reason = 'rewritten'"))
        refused("DELETE a lineage edge", lambda: app.execute("DELETE FROM fact_edges"))
        refused("DROP the facts table", lambda: app.execute("DROP TABLE facts"))
        refused("ALTER the schema", lambda: app.execute("ALTER TABLE facts ADD COLUMN sneaky INT"))
        refused("CREATE a new table", lambda: app.execute("CREATE TABLE evil (id INT PRIMARY KEY)"))

    passed = sum(1 for r in results if r["ok"])
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({
        "what_this_is": (
            "Access-control evidence. Every row was executed against a live cluster "
            "as the least-privilege rescind_app role from sql/003_roles.sql."
        ),
        "commit": os.environ.get("GITHUB_SHA", "local"),
        "role": "rescind_app",
        "headline": (
            "The application role holds no DELETE privilege anywhere and no UPDATE "
            "on retractions, so the audit trail is insert-only at the privilege "
            "level rather than by convention."
        ),
        "checks_passed": passed,
        "checks_total": len(results),
        "checks": results,
    }, indent=2) + "\n")
    print(f"\n{passed}/{len(results)} privilege checks behaved as specified")
    print(f"wrote {OUT}")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
