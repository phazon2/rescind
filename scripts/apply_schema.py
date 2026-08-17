#!/usr/bin/env python3
"""Apply the Rescind schema to the cluster named by RESCIND_DATABASE_URL.

The bootstrap file (the vector-index cluster setting) is applied tolerantly:
on some managed clusters it is not user-settable, and retrieval remains correct
without it -- just unindexed. Everything in 001_schema.sql is applied strictly.
"""

from __future__ import annotations

import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from rescind.db import connect  # noqa: E402

SQL_DIR = pathlib.Path(__file__).resolve().parent.parent / "sql"


def statements(sql_text: str) -> list[str]:
    """Split a SQL file into statements.

    Comments are stripped first: several of ours contain semicolons, which would
    otherwise split a statement in half.
    """
    without_comments = re.sub(r"--[^\n]*", "", sql_text)
    return [s.strip() for s in without_comments.split(";") if s.strip()]


def apply_file(conn, path: pathlib.Path, strict: bool = True) -> list[str]:
    problems: list[str] = []
    for statement in statements(path.read_text()):
        try:
            conn.execute(statement)
        except Exception as exc:  # noqa: BLE001
            label = " ".join(statement.split())[:90]
            if strict:
                print(f"  FAILED: {label}\n    {type(exc).__name__}: {exc}")
                raise
            problems.append(f"{label} -> {type(exc).__name__}: {exc}")
            print(f"  tolerated failure: {label}\n    {type(exc).__name__}: {exc}")
    return problems


def main() -> int:
    with connect() as conn:
        version = conn.execute("SELECT version() AS v").fetchone()["v"]
        print(f"cluster: {version}")

        print("\napplying sql/000_bootstrap.sql (tolerant)")
        tolerated = apply_file(conn, SQL_DIR / "000_bootstrap.sql", strict=False)
        if not tolerated:
            print("  ok")

        print("\napplying sql/001_schema.sql (strict)")
        apply_file(conn, SQL_DIR / "001_schema.sql", strict=True)
        print("  ok")

        tables = [
            r["table_name"]
            for r in conn.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' ORDER BY table_name"
            ).fetchall()
        ]
        print(f"\ntables: {', '.join(tables)}")

        indexes = [
            r["index_name"]
            for r in conn.execute(
                "SELECT DISTINCT index_name FROM information_schema.statistics "
                "WHERE table_name = 'facts' ORDER BY index_name"
            ).fetchall()
        ]
        print(f"indexes on facts: {', '.join(indexes)}")

        if tolerated:
            print(
                "\nNOTE: the vector-index cluster setting was not applied. "
                "Retrieval stays correct but may be unindexed. See docs/LIMITS.md."
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
