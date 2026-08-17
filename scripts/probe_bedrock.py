#!/usr/bin/env python3
"""Prove the AWS Bedrock path for real, and write the evidence to ci/bedrock.json.

This is the one thing the offline suite cannot certify: whether
amazon.titan-embed-text-v2:0 actually returns the 1024 dimensions the schema
hardcodes as VECTOR(1024), and whether Claude returns a verdict this code can
parse.

Run with real AWS credentials and RESCIND_OFFLINE unset.
"""

from __future__ import annotations

import json
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from rescind import bedrock  # noqa: E402
from rescind.config import BEDROCK_EMBED_MODEL, BEDROCK_REASONING_MODEL, EMBED_DIM  # noqa: E402
from rescind.db import connect, to_vector  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parent.parent / "ci" / "bedrock.json"

SAMPLE = (
    "Certificate of Analysis for lot LOT-2026-0619-NV: Cronobacter sakazakii "
    "not detected in 30 of 30 sampled tins; lot passed release testing."
)
QUESTION = "May we release lot LOT-2026-0619-NV to Meridian Foods DC-7?"


def main() -> int:
    if bedrock.offline_forced():
        print("RESCIND_OFFLINE is set; this script must run against live AWS.", file=sys.stderr)
        return 1

    results: list[dict] = []
    ok = True

    # --- 1. Titan really returns EMBED_DIM dimensions -----------------------
    try:
        vector = bedrock.embed(SAMPLE)
        dims = len(vector)
        norm = sum(v * v for v in vector) ** 0.5
        passed = dims == EMBED_DIM
        results.append({
            "check": "titan_dimensions",
            "model": BEDROCK_EMBED_MODEL,
            "passed": passed,
            "detail": f"{dims} dimensions, L2 norm {norm:.4f}",
        })
        print(f"  [{'OK' if passed else 'FAIL'}] Titan returned {dims} dims (norm {norm:.4f})")
        ok &= passed
    except Exception as exc:  # noqa: BLE001
        ok = False
        vector = None
        results.append({"check": "titan_dimensions", "passed": False, "detail": repr(exc)[:300]})
        print(f"  [FAIL] Titan: {exc}")

    # --- 2. A real Titan vector round-trips through the schema --------------
    if vector is not None and len(vector) == EMBED_DIM:
        try:
            with connect() as conn:
                conn.execute("DROP TABLE IF EXISTS bedrock_probe")
                conn.execute(
                    f"CREATE TABLE bedrock_probe (id INT PRIMARY KEY, v VECTOR({EMBED_DIM}))"
                )
                conn.execute(
                    f"INSERT INTO bedrock_probe VALUES (1, %s::VECTOR({EMBED_DIM}))",
                    (to_vector(vector),),
                )
                row = conn.execute(
                    f"SELECT v <-> %s::VECTOR({EMBED_DIM}) AS d FROM bedrock_probe",
                    (to_vector(vector),),
                ).fetchone()
                d = float(list(row.values())[0])
                conn.execute("DROP TABLE bedrock_probe")
            passed = d < 1e-6
            results.append({
                "check": "titan_vector_roundtrip",
                "passed": passed,
                "detail": f"self-distance {d:.8f} (expected ~0)",
            })
            print(f"  [{'OK' if passed else 'FAIL'}] round-trip self-distance {d:.8f}")
            ok &= passed
        except Exception as exc:  # noqa: BLE001
            ok = False
            results.append({"check": "titan_vector_roundtrip", "passed": False, "detail": repr(exc)[:300]})
            print(f"  [FAIL] round-trip: {exc}")

    # --- 3. Claude returns a verdict this code can parse --------------------
    try:
        verdict = bedrock.reason(QUESTION, [SAMPLE])
        passed = verdict["verdict"] in {"release", "hold"} and not verdict.get("offline", True)
        results.append({
            "check": "claude_verdict_parses",
            "model": BEDROCK_REASONING_MODEL,
            "passed": passed,
            "detail": f"verdict={verdict['verdict']!r} offline={verdict.get('offline')}",
        })
        print(f"  [{'OK' if passed else 'FAIL'}] Claude verdict: {verdict['verdict']}")
        ok &= passed
    except Exception as exc:  # noqa: BLE001
        ok = False
        results.append({"check": "claude_verdict_parses", "passed": False, "detail": repr(exc)[:300]})
        print(f"  [FAIL] Claude: {exc}")

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({
        "what_this_is": (
            "Evidence that the AWS Bedrock path was exercised against live AWS, "
            "not the deterministic offline stand-in."
        ),
        "commit": os.environ.get("GITHUB_SHA", "local"),
        "region": os.environ.get("AWS_REGION", "unset"),
        "checks": results,
        "all_passed": ok,
    }, indent=2) + "\n")
    print(f"\nwrote {OUT}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
