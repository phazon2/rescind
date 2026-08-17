#!/usr/bin/env python3
"""Seed the recall scenario: the lot, the shipment, and the agent's memory of it.

Northvale Dairy Co-op -> Meridian Foods DC-7. Three first-hand observations and
three conclusions the agent derived from them, with real lineage. Retracting the
Certificate of Analysis brings two of the three conclusions down.
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from rescind.db import connect  # noqa: E402
from rescind.memory import assert_fact, derive_fact  # noqa: E402
from rescind.topics import topic_vector  # noqa: E402

LOT = "LOT-2026-0619-NV"
SQL_DIR = pathlib.Path(__file__).resolve().parent.parent / "sql"

# The question the recall coordinator actually asks.
QUESTION = "May we release lot LOT-2026-0619-NV to Meridian Foods DC-7?"
QUESTION_TOPICS = {"lot_release_safety": 1.0}

OBSERVATIONS = [
    {
        "key": "coa",
        "claim": (
            "Certificate of Analysis for lot LOT-2026-0619-NV: Cronobacter "
            "sakazakii not detected in 30 of 30 sampled tins."
        ),
        "source": "Northvale Dairy Co-op QA, CoA #4471, issued 2026-06-24",
        "topics": {"lot_release_safety": 0.95, "microbiological_testing": 0.31},
    },
    {
        "key": "cold_chain",
        "claim": (
            "Cold chain log for pallet NV-8841 held 2.1-6.8 C across the full "
            "41-hour transit with no excursions."
        ),
        "source": "Carrier telemetry, sensor #NV-9134",
        "topics": {"lot_release_safety": 0.95, "cold_chain": 0.31},
    },
    {
        "key": "audit",
        "claim": (
            "Supplier audit of Northvale Dairy Co-op closed 2026-05-14 with no "
            "major findings."
        ),
        "source": "SGS third-party audit report #22-NV",
        "topics": {"supplier_standing": 0.95, "supplier_audit": 0.31},
    },
]

DERIVED = [
    {
        "key": "good_standing",
        "claim": "Northvale Dairy Co-op is a supplier in good standing.",
        "source": "rescind-agent: derived from supplier audit",
        "topics": {"supplier_standing": 0.97, "lot_release_safety": 0.24},
        "parents": ["audit"],
    },
    {
        "key": "meets_criteria",
        "claim": (
            "Lot LOT-2026-0619-NV meets microbiological release criteria."
        ),
        "source": "rescind-agent: derived from CoA #4471 and cold chain telemetry",
        "topics": {"lot_release_safety": 0.97, "microbiological_testing": 0.24},
        "parents": ["coa", "cold_chain"],
    },
    {
        "key": "cleared",
        "claim": (
            "Lot LOT-2026-0619-NV is cleared for release to Meridian Foods DC-7."
        ),
        "source": "rescind-agent: derived from release criteria and supplier standing",
        "topics": {"lot_release_safety": 0.98, "logistics": 0.20},
        "parents": ["meets_criteria", "good_standing"],
    },
]


def main() -> int:
    with connect() as conn:
        sql = (SQL_DIR / "002_seed.sql").read_text()
        import re

        for statement in [
            s.strip() for s in re.sub(r"--[^\n]*", "", sql).split(";") if s.strip()
        ]:
            conn.execute(statement)
        print("seeded lots and shipments")

        ids: dict[str, str] = {}
        for obs in OBSERVATIONS:
            ids[obs["key"]] = assert_fact(
                conn, LOT, obs["claim"], obs["source"], topic_vector(obs["topics"])
            )
            print(f"  observation  {obs['key']:15s} {ids[obs['key']]}")

        for der in DERIVED:
            ids[der["key"]] = derive_fact(
                conn,
                LOT,
                der["claim"],
                der["source"],
                topic_vector(der["topics"]),
                [ids[p] for p in der["parents"]],
            )
            print(f"  derived      {der['key']:15s} {ids[der['key']]}")

        counts = conn.execute(
            "SELECT (SELECT count(*) FROM facts) AS facts, "
            "(SELECT count(*) FROM fact_edges) AS edges"
        ).fetchone()
        print(f"\n{counts['facts']} facts, {counts['edges']} lineage edges")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
