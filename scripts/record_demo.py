#!/usr/bin/env python3
"""Run the full recall scenario against the real cluster and record the result.

Writes web/data.json, which drives the demo page. Every number, id, hybrid
logical clock and claim on that page comes from this run against a real
CockroachDB cluster -- the page replays a real transaction rather than
illustrating one.

The sequence, which is exactly the sequence in the video:

  1. the agent is asked whether lot LOT-2026-0619-NV may ship, and answers
     "release" on four supporting memories;
  2. Northvale issues a recall on the Certificate of Analysis;
  3. one transaction retracts the CoA and everything derived from it, and flags
     the standing decision for human review;
  4. the identical question is now REFUSED, because live support fell below
     threshold;
  5. AS OF SYSTEM TIME replay shows exactly what the agent knew when it said
     "release", and what it no longer knows.
"""

from __future__ import annotations

import json
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from rescind import agent, memory  # noqa: E402
from rescind.config import (  # noqa: E402
    MAX_SUPPORTING_DISTANCE,
    MIN_SUPPORTING_FACTS,
)
from rescind.db import connect  # noqa: E402
from rescind.topics import topic_vector  # noqa: E402
from scripts.seed import LOT, QUESTION, QUESTION_TOPICS  # noqa: E402

RECALL_REASON = (
    "FDA Class II recall notice: Cronobacter sakazakii detected in a retained "
    "sample from the same production run. CoA #4471 withdrawn by Northvale QA."
)
OUT = pathlib.Path(__file__).resolve().parent.parent / "web" / "data.json"


def _fact_rows(conn):
    rows = conn.execute(
        """
        SELECT id, kind, claim, source, retracted, retracted_reason
        FROM facts WHERE lot_id = %s ORDER BY asserted_at
        """,
        (LOT,),
    ).fetchall()
    return [
        {
            "id": str(r["id"]),
            "kind": r["kind"],
            "claim": r["claim"],
            "source": r["source"],
            "retracted": bool(r["retracted"]),
            "retracted_reason": r["retracted_reason"],
        }
        for r in rows
    ]


def _lineage(conn):
    rows = conn.execute(
        """
        SELECT e.parent_id, e.child_id
        FROM fact_edges e JOIN facts f ON f.id = e.child_id
        WHERE f.lot_id = %s
        """,
        (LOT,),
    ).fetchall()
    return [{"parent": str(r["parent_id"]), "child": str(r["child_id"])} for r in rows]


def _decision_payload(decision):
    return {
        "id": decision.id,
        "question": decision.question,
        "verdict": decision.verdict,
        "rationale": decision.rationale,
        "decided_hlc": decision.decided_hlc,
        "model_id": decision.model_id,
        "offline_mode": decision.offline,
        "supporting": [
            {
                "id": r.id,
                "claim": r.claim,
                "source": r.source,
                "distance": round(r.distance, 4),
            }
            for r in decision.supporting
        ],
    }


def main() -> int:
    query_vec = topic_vector(QUESTION_TOPICS)

    # The question must be embedded in the SAME space as the seeded facts. In
    # offline mode that space is the topic space in rescind/topics.py, so the
    # question is embedded with topic weights rather than through the default
    # lexical stand-in. With AWS credentials both the facts and the question go
    # through Titan and this override is unnecessary. Stated in docs/LIMITS.md.
    def demo_embedder(_question: str):
        return query_vec

    with connect() as conn:
        version = list(conn.execute("SELECT version() AS v").fetchone().values())[0]
        lot = conn.execute(
            "SELECT * FROM lots WHERE lot_id = %s", (LOT,)
        ).fetchone()
        shipment = conn.execute(
            "SELECT * FROM shipments WHERE lot_id = %s", (LOT,)
        ).fetchone()

        # --- 1. the agent answers -------------------------------------------
        before_facts = _fact_rows(conn)
        decision = agent.ask(conn, LOT, QUESTION, embedder=demo_embedder)
        print(f"1. agent answered: {decision.verdict} "
              f"on {len(decision.supporting)} supporting memories")

        plan = memory.explain_retrieval(conn, LOT, query_vec)

        # --- 2/3. the recall, and the cascade -------------------------------
        coa = next(f for f in before_facts if "CoA #4471" in f["source"])
        conn.execute(
            "UPDATE lots SET status = 'recalled', recalled_at = now() WHERE lot_id = %s",
            (LOT,),
        )
        receipt = memory.retract(
            conn, LOT, [coa["id"]], RECALL_REASON, actor="d.radrigan"
        )
        print(f"2. retracted {receipt.facts_retracted} facts "
              f"({receipt.cascade_depth_beyond_roots} by cascade), "
              f"flagged {receipt.decisions_flagged} decision(s)")

        # --- 4. the same question, now refused ------------------------------
        second = agent.ask(conn, LOT, QUESTION, embedder=demo_embedder)
        print(f"3. same question now: {second.verdict}")

        # --- 5. time-travel proof -------------------------------------------
        report = memory.replay(conn, decision.id)
        print(f"4. replay at hlc {report.decided_hlc}: "
              f"knew {len(report.facts_then)}, knows {len(report.facts_now)}, "
              f"withdrawn {len(report.withdrawn_since)}")

        payload = {
            "recorded_from": {
                "note": (
                    "Every value on this page was produced by "
                    "scripts/record_demo.py running against a real CockroachDB "
                    "cluster in CI. Nothing here is illustrative."
                ),
                "cockroachdb_version": version,
                "commit": os.environ.get("GITHUB_SHA", "local"),
                "run_url": (
                    f"{os.environ.get('GITHUB_SERVER_URL', 'https://github.com')}/"
                    f"{os.environ.get('GITHUB_REPOSITORY', 'phazon2/rescind')}/actions/runs/"
                    f"{os.environ.get('GITHUB_RUN_ID', '')}"
                ),
                "embeddings": (
                    "deterministic topic-anchored stand-ins, not AWS Titan -- see "
                    "docs/LIMITS.md"
                )
                if os.environ.get("RESCIND_OFFLINE", "").lower() in {"1", "true", "yes"}
                else "amazon.titan-embed-text-v2:0",
            },
            "thresholds": {
                "min_supporting_facts": MIN_SUPPORTING_FACTS,
                "max_supporting_distance": MAX_SUPPORTING_DISTANCE,
            },
            "lot": {
                "lot_id": lot["lot_id"],
                "product_name": lot["product_name"],
                "supplier": lot["supplier"],
                "manufactured_on": str(lot["manufactured_on"]),
                "status": "recalled",
            },
            "shipment": {
                "shipment_id": shipment["shipment_id"],
                "destination": shipment["destination"],
                "units": shipment["units"],
                "status": shipment["status"],
            },
            "before": {
                "facts": before_facts,
                "decision": _decision_payload(decision),
                "retrieval_plan": plan,
            },
            "retraction": {
                "retraction_id": receipt.retraction_id,
                "reason": receipt.reason,
                "actor": receipt.actor,
                "root_fact_ids": receipt.root_fact_ids,
                "retracted_fact_ids": receipt.retracted_fact_ids,
                "facts_retracted": receipt.facts_retracted,
                "cascade_beyond_roots": receipt.cascade_depth_beyond_roots,
                "decisions_flagged": receipt.decisions_flagged,
                "retracted_hlc": receipt.retracted_hlc,
            },
            "after": {
                "facts": _fact_rows(conn),
                "decision": _decision_payload(second),
                "open_reviews": agent.open_reviews(conn, LOT),
            },
            "replay": {
                "decided_hlc": report.decided_hlc,
                "verdict_recorded": report.verdict,
                "needs_review": report.needs_review,
                "review_reason": report.review_reason,
                "knew_then": [
                    {"claim": f["claim"], "source": f["source"]} for f in report.facts_then
                ],
                "knows_now": [
                    {"claim": f["claim"], "source": f["source"]} for f in report.facts_now
                ],
                "withdrawn_since": [
                    {"claim": f["claim"], "source": f["source"]}
                    for f in report.withdrawn_since
                ],
            },
            "lineage": _lineage(conn),
        }

    OUT.parent.mkdir(exist_ok=True)
    serialised = json.dumps(payload, indent=2, default=str)
    OUT.write_text(serialised + "\n")
    print(f"\nwrote {OUT}")

    # Also emit the same payload as a script file. Loading the data via a <script>
    # tag rather than fetch() means the demo page works when opened directly from
    # disk and when served from any host, with no CORS dependency.
    js = OUT.parent / "data.js"
    js.write_text("window.RESCIND_DATA = " + serialised + ";\n")
    print(f"wrote {js}")

    # Guard rails: if the recorded scenario stops telling the story, fail loudly
    # rather than shipping a demo page that quietly says nothing.
    assert payload["before"]["decision"]["verdict"] == "release", "expected an initial release"
    assert payload["after"]["decision"]["verdict"] == "refused", "expected a refusal after recall"
    assert payload["retraction"]["cascade_beyond_roots"] >= 1, "expected a real cascade"
    assert payload["retraction"]["decisions_flagged"] >= 1, "expected a flagged decision"
    assert len(payload["replay"]["withdrawn_since"]) >= 1, "expected a withdrawn memory"
    print("scenario assertions passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
