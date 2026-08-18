window.RESCIND_DATA = {
  "recorded_from": {
    "note": "Every value on this page was produced by scripts/record_demo.py running against a real CockroachDB cluster in CI. Nothing here is illustrative.",
    "cockroachdb_version": "CockroachDB CCL v25.3.0 (x86_64-pc-linux-gnu, built 2025/08/14 18:25:15, go1.23.7 X:nocoverageredesign)",
    "commit": "d9572722e60b081f6c30a6c89d1701b00abeff2f",
    "run_url": "https://github.com/phazon2/rescind/actions/runs/32087581404",
    "embeddings": "deterministic topic-anchored stand-ins, not AWS Titan -- see docs/LIMITS.md"
  },
  "thresholds": {
    "min_supporting_facts": 2,
    "max_supporting_distance": 0.55
  },
  "lot": {
    "lot_id": "LOT-2026-0619-NV",
    "product_name": "Infant Formula, Stage 1, 400g tin",
    "supplier": "Northvale Dairy Co-op",
    "manufactured_on": "2026-06-19",
    "status": "recalled"
  },
  "shipment": {
    "shipment_id": "SHP-88412",
    "destination": "Meridian Foods DC-7, Sacramento CA",
    "units": 4800,
    "status": "staged"
  },
  "before": {
    "facts": [
      {
        "id": "bad538b4-a368-4cd1-a119-d69f73c7f41f",
        "kind": "observation",
        "claim": "Certificate of Analysis for lot LOT-2026-0619-NV: Cronobacter sakazakii not detected in 30 of 30 sampled tins; lot passed release testing.",
        "source": "Northvale Dairy Co-op QA, CoA #4471, issued 2026-06-24",
        "retracted": false,
        "retracted_reason": null
      },
      {
        "id": "671309f6-e3e9-4454-9772-6ab31a85df36",
        "kind": "observation",
        "claim": "Cold chain log for pallet NV-8841 held 2.1-6.8 C across the full 41-hour transit with no excursions, within specification throughout.",
        "source": "Carrier telemetry, sensor #NV-9134",
        "retracted": false,
        "retracted_reason": null
      },
      {
        "id": "c83e1511-448d-45dd-8518-caab4c94c7e6",
        "kind": "observation",
        "claim": "Supplier audit of Northvale Dairy Co-op closed 2026-05-14 with no major findings.",
        "source": "SGS third-party audit report #22-NV",
        "retracted": false,
        "retracted_reason": null
      },
      {
        "id": "35a37410-f397-4d42-a827-6119db74c15b",
        "kind": "derived",
        "claim": "Northvale Dairy Co-op is a supplier in good standing.",
        "source": "rescind-agent: derived from supplier audit",
        "retracted": false,
        "retracted_reason": null
      },
      {
        "id": "31a2e6dd-3a14-46eb-ab49-834a21450721",
        "kind": "derived",
        "claim": "Lot LOT-2026-0619-NV meets microbiological release criteria.",
        "source": "rescind-agent: derived from CoA #4471 and cold chain telemetry",
        "retracted": false,
        "retracted_reason": null
      },
      {
        "id": "8dfa277a-757b-4a4c-b5a0-72d238afda8e",
        "kind": "derived",
        "claim": "Lot LOT-2026-0619-NV is cleared for release to Meridian Foods DC-7.",
        "source": "rescind-agent: derived from release criteria and supplier standing",
        "retracted": false,
        "retracted_reason": null
      }
    ],
    "decision": {
      "id": "1e3e7d65-1cc8-4c43-a8cb-18622cada448",
      "question": "May we release lot LOT-2026-0619-NV to Meridian Foods DC-7?",
      "verdict": "release",
      "rationale": "Offline reasoning: every supporting record for this lot reports a passing result and none reports a recall or contamination finding.",
      "decided_hlc": "1787015768197947783.0000000000",
      "model_id": "offline-deterministic",
      "offline_mode": true,
      "supporting": [
        {
          "id": "8dfa277a-757b-4a4c-b5a0-72d238afda8e",
          "claim": "Lot LOT-2026-0619-NV is cleared for release to Meridian Foods DC-7.",
          "source": "rescind-agent: derived from release criteria and supplier standing",
          "distance": 0.201
        },
        {
          "id": "31a2e6dd-3a14-46eb-ab49-834a21450721",
          "claim": "Lot LOT-2026-0619-NV meets microbiological release criteria.",
          "source": "rescind-agent: derived from CoA #4471 and cold chain telemetry",
          "distance": 0.242
        },
        {
          "id": "671309f6-e3e9-4454-9772-6ab31a85df36",
          "claim": "Cold chain log for pallet NV-8841 held 2.1-6.8 C across the full 41-hour transit with no excursions, within specification throughout.",
          "source": "Carrier telemetry, sensor #NV-9134",
          "distance": 0.3141
        },
        {
          "id": "bad538b4-a368-4cd1-a119-d69f73c7f41f",
          "claim": "Certificate of Analysis for lot LOT-2026-0619-NV: Cronobacter sakazakii not detected in 30 of 30 sampled tins; lot passed release testing.",
          "source": "Northvale Dairy Co-op QA, CoA #4471, issued 2026-06-24",
          "distance": 0.3141
        }
      ]
    },
    "retrieval_plan": "distribution: local\nvectorized: true\n\n\u2022 top-k\n\u2502 order: +column16\n\u2502 k: 5\n\u2502\n\u2514\u2500\u2500 \u2022 render\n    \u2502\n    \u2514\u2500\u2500 \u2022 lookup join\n        \u2502 table: facts@facts_pkey\n        \u2502 equality: (id) = (id)\n        \u2502 equality cols are key\n        \u2502\n        \u2514\u2500\u2500 \u2022 vector search\n              table: facts@facts_live_by_lot\n              target count: 5\n              prefix spans: [/'LOT-2026-0619-NV'/false - /'LOT-2026-0619-NV'/false]\n\nindex recommendations: 1\n1. type: index creation\n   SQL command: CREATE INDEX ON rescind.public.facts (lot_id) STORING (claim, embedding, retracted);"
  },
  "retraction": {
    "retraction_id": "19a69494-d9d6-4ef7-a6b9-3d49bfa9c502",
    "reason": "FDA Class II recall notice: Cronobacter sakazakii detected in a retained sample from the same production run. CoA #4471 withdrawn by Northvale QA.",
    "actor": "d.radrigan",
    "root_fact_ids": [
      "bad538b4-a368-4cd1-a119-d69f73c7f41f"
    ],
    "retracted_fact_ids": [
      "31a2e6dd-3a14-46eb-ab49-834a21450721",
      "8dfa277a-757b-4a4c-b5a0-72d238afda8e",
      "bad538b4-a368-4cd1-a119-d69f73c7f41f"
    ],
    "facts_retracted": 3,
    "cascade_beyond_roots": 2,
    "decisions_flagged": 1,
    "retracted_hlc": "1787015768206707682.0000000000"
  },
  "after": {
    "facts": [
      {
        "id": "bad538b4-a368-4cd1-a119-d69f73c7f41f",
        "kind": "observation",
        "claim": "Certificate of Analysis for lot LOT-2026-0619-NV: Cronobacter sakazakii not detected in 30 of 30 sampled tins; lot passed release testing.",
        "source": "Northvale Dairy Co-op QA, CoA #4471, issued 2026-06-24",
        "retracted": true,
        "retracted_reason": "FDA Class II recall notice: Cronobacter sakazakii detected in a retained sample from the same production run. CoA #4471 withdrawn by Northvale QA."
      },
      {
        "id": "671309f6-e3e9-4454-9772-6ab31a85df36",
        "kind": "observation",
        "claim": "Cold chain log for pallet NV-8841 held 2.1-6.8 C across the full 41-hour transit with no excursions, within specification throughout.",
        "source": "Carrier telemetry, sensor #NV-9134",
        "retracted": false,
        "retracted_reason": null
      },
      {
        "id": "c83e1511-448d-45dd-8518-caab4c94c7e6",
        "kind": "observation",
        "claim": "Supplier audit of Northvale Dairy Co-op closed 2026-05-14 with no major findings.",
        "source": "SGS third-party audit report #22-NV",
        "retracted": false,
        "retracted_reason": null
      },
      {
        "id": "35a37410-f397-4d42-a827-6119db74c15b",
        "kind": "derived",
        "claim": "Northvale Dairy Co-op is a supplier in good standing.",
        "source": "rescind-agent: derived from supplier audit",
        "retracted": false,
        "retracted_reason": null
      },
      {
        "id": "31a2e6dd-3a14-46eb-ab49-834a21450721",
        "kind": "derived",
        "claim": "Lot LOT-2026-0619-NV meets microbiological release criteria.",
        "source": "rescind-agent: derived from CoA #4471 and cold chain telemetry",
        "retracted": true,
        "retracted_reason": "FDA Class II recall notice: Cronobacter sakazakii detected in a retained sample from the same production run. CoA #4471 withdrawn by Northvale QA."
      },
      {
        "id": "8dfa277a-757b-4a4c-b5a0-72d238afda8e",
        "kind": "derived",
        "claim": "Lot LOT-2026-0619-NV is cleared for release to Meridian Foods DC-7.",
        "source": "rescind-agent: derived from release criteria and supplier standing",
        "retracted": true,
        "retracted_reason": "FDA Class II recall notice: Cronobacter sakazakii detected in a retained sample from the same production run. CoA #4471 withdrawn by Northvale QA."
      }
    ],
    "decision": {
      "id": "adb5ec2e-0c3d-49dd-9e39-f262a15abd5c",
      "question": "May we release lot LOT-2026-0619-NV to Meridian Foods DC-7?",
      "verdict": "refused",
      "rationale": "Refused: 1 live supporting record(s) within distance 0.55 for this lot, but 2 are required. Rescind will not answer from insufficient memory. Absence of evidence is not evidence of safety -- this lot is not cleared.",
      "decided_hlc": "1787015768218471492.0000000000",
      "model_id": "none-refused-before-model-call",
      "offline_mode": false,
      "supporting": [
        {
          "id": "671309f6-e3e9-4454-9772-6ab31a85df36",
          "claim": "Cold chain log for pallet NV-8841 held 2.1-6.8 C across the full 41-hour transit with no excursions, within specification throughout.",
          "source": "Carrier telemetry, sensor #NV-9134",
          "distance": 0.3141
        }
      ]
    },
    "open_reviews": [
      {
        "id": "1e3e7d65-1cc8-4c43-a8cb-18622cada448",
        "lot_id": "LOT-2026-0619-NV",
        "question": "May we release lot LOT-2026-0619-NV to Meridian Foods DC-7?",
        "verdict": "release",
        "rationale": "Offline reasoning: every supporting record for this lot reports a passing result and none reports a recall or contamination finding.",
        "review_reason": "supporting memory retracted: FDA Class II recall notice: Cronobacter sakazakii detected in a retained sample from the same production run. CoA #4471 withdrawn by Northvale QA.",
        "decided_at": "2026-08-18 01:16:08.197934+00:00"
      }
    ]
  },
  "replay": {
    "decided_hlc": "1787015768197947783.0000000000",
    "verdict_recorded": "release",
    "needs_review": true,
    "review_reason": "supporting memory retracted: FDA Class II recall notice: Cronobacter sakazakii detected in a retained sample from the same production run. CoA #4471 withdrawn by Northvale QA.",
    "knew_then": [
      {
        "claim": "Lot LOT-2026-0619-NV is cleared for release to Meridian Foods DC-7.",
        "source": "rescind-agent: derived from release criteria and supplier standing"
      },
      {
        "claim": "Lot LOT-2026-0619-NV meets microbiological release criteria.",
        "source": "rescind-agent: derived from CoA #4471 and cold chain telemetry"
      },
      {
        "claim": "Cold chain log for pallet NV-8841 held 2.1-6.8 C across the full 41-hour transit with no excursions, within specification throughout.",
        "source": "Carrier telemetry, sensor #NV-9134"
      },
      {
        "claim": "Certificate of Analysis for lot LOT-2026-0619-NV: Cronobacter sakazakii not detected in 30 of 30 sampled tins; lot passed release testing.",
        "source": "Northvale Dairy Co-op QA, CoA #4471, issued 2026-06-24"
      }
    ],
    "knows_now": [
      {
        "claim": "Cold chain log for pallet NV-8841 held 2.1-6.8 C across the full 41-hour transit with no excursions, within specification throughout.",
        "source": "Carrier telemetry, sensor #NV-9134"
      }
    ],
    "withdrawn_since": [
      {
        "claim": "Lot LOT-2026-0619-NV is cleared for release to Meridian Foods DC-7.",
        "source": "rescind-agent: derived from release criteria and supplier standing"
      },
      {
        "claim": "Lot LOT-2026-0619-NV meets microbiological release criteria.",
        "source": "rescind-agent: derived from CoA #4471 and cold chain telemetry"
      },
      {
        "claim": "Certificate of Analysis for lot LOT-2026-0619-NV: Cronobacter sakazakii not detected in 30 of 30 sampled tins; lot passed release testing.",
        "source": "Northvale Dairy Co-op QA, CoA #4471, issued 2026-06-24"
      }
    ]
  },
  "lineage": [
    {
      "parent": "671309f6-e3e9-4454-9772-6ab31a85df36",
      "child": "31a2e6dd-3a14-46eb-ab49-834a21450721"
    },
    {
      "parent": "bad538b4-a368-4cd1-a119-d69f73c7f41f",
      "child": "31a2e6dd-3a14-46eb-ab49-834a21450721"
    },
    {
      "parent": "c83e1511-448d-45dd-8518-caab4c94c7e6",
      "child": "35a37410-f397-4d42-a827-6119db74c15b"
    },
    {
      "parent": "31a2e6dd-3a14-46eb-ab49-834a21450721",
      "child": "8dfa277a-757b-4a4c-b5a0-72d238afda8e"
    },
    {
      "parent": "35a37410-f397-4d42-a827-6119db74c15b",
      "child": "8dfa277a-757b-4a4c-b5a0-72d238afda8e"
    }
  ]
};
