#!/usr/bin/env python3
"""Minimal repro harness for the SQL-level questions Rescind depends on.

Runs the smallest possible statement for each risky construct and prints the
exact error when one fails, so a CI round trip pinpoints the cause instead of
burying it. Never fails the build.
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from rescind.config import EMBED_DIM  # noqa: E402
from rescind.db import connect, to_vector  # noqa: E402

VEC = to_vector([1.0] + [0.0] * (EMBED_DIM - 1))


def check(label, fn):
    try:
        result = fn()
        print(f"  [ OK ] {label}: {result}")
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"  [FAIL] {label}: {type(exc).__name__}: {exc}")
        return False


def main() -> int:
    with connect() as conn:
        conn.execute("DROP TABLE IF EXISTS smoke_vec")
        conn.execute(
            f"CREATE TABLE smoke_vec (id INT PRIMARY KEY, v VECTOR({EMBED_DIM}) NOT NULL)"
        )

        print("vector insert paths:")

        def parameterised():
            conn.execute(
                f"INSERT INTO smoke_vec (id, v) VALUES (1, %s::VECTOR({EMBED_DIM}))",
                (VEC,),
            )
            return "parameter cast accepted"

        def parameterised_no_cast():
            conn.execute("INSERT INTO smoke_vec (id, v) VALUES (2, %s)", (VEC,))
            return "bare parameter accepted"

        def inline_literal():
            conn.execute(
                f"INSERT INTO smoke_vec (id, v) VALUES (3, '{VEC}'::VECTOR({EMBED_DIM}))"
            )
            return "inline literal accepted"

        results = {
            "parameterised %s::VECTOR(n)": check("parameterised %s::VECTOR(n)", parameterised),
            "bare parameter %s": check("bare parameter %s", parameterised_no_cast),
            "inline literal": check("inline literal", inline_literal),
        }

        print("\ndistance operator paths:")

        def distance_param():
            row = conn.execute(
                f"SELECT v <-> %s::VECTOR({EMBED_DIM}) AS d FROM smoke_vec LIMIT 1",
                (VEC,),
            ).fetchone()
            return f"distance {list(row.values())[0]}"

        def distance_inline():
            row = conn.execute(
                f"SELECT v <-> '{VEC}'::VECTOR({EMBED_DIM}) AS d FROM smoke_vec LIMIT 1"
            ).fetchone()
            return f"distance {list(row.values())[0]}"

        check("parameterised <->", distance_param)
        check("inline <->", distance_inline)

        print("\narray parameter paths (used by the retraction cascade):")

        def uuid_array():
            row = conn.execute(
                "SELECT count(*) AS n FROM (SELECT unnest(%s::UUID[]) AS id)",
                ([ "00000000-0000-0000-0000-000000000001" ],),
            ).fetchone()
            return f"unnest returned {row['n']} row(s)"

        check("unnest(%s::UUID[])", uuid_array)

        conn.execute("DROP TABLE smoke_vec")

        print(
            "\nsummary: "
            + ", ".join(f"{k}={'ok' if v else 'FAIL'}" for k, v in results.items())
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
