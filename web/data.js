window.RESCIND_DATA = {
  "recorded_from": {
    "note": "Every value on this page was produced by scripts/record_demo.py running against a real CockroachDB cluster in CI. Nothing here is illustrative.",
    "cockroachdb_version": "CockroachDB CCL v25.3.0 (x86_64-pc-linux-gnu, built 2025/08/14 18:25:15, go1.23.7 X:nocoverageredesign)",
    "commit": "aa6c83e8680afe129e21519ceb3e82fb3dcb8646",
    "run_url": "https://github.com/phazon2/rescind/actions/runs/32037806883",
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
        "id": "824344d5-b477-4e4a-8580-1ec3e819b7f2",
        "kind": "observation",
        "claim": "Certificate of Analysis for lot LOT-2026-0619-NV: Cronobacter sakazakii not detected in 30 of 30 sampled tins; lot passed release testing.",
        "source": "Northvale Dairy Co-op QA, CoA #4471, issued 2026-06-24",
        "retracted": false,
        "retracted_reason": null
      },
      {
        "id": "70ff044d-44fa-43dc-9ae7-4d32a4d5251a",
        "kind": "observation",
        "claim": "Cold chain log for pallet NV-8841 held 2.1-6.8 C across the full 41-hour transit with no excursions, within specification throughout.",
        "source": "Carrier telemetry, sensor #NV-9134",
        "retracted": false,
        "retracted_reason": null
      },
      {
        "id": "54cf6ded-fddc-4068-abeb-7b0017f3821d",
        "kind": "observation",
        "claim": "Supplier audit of Northvale Dairy Co-op closed 2026-05-14 with no major findings.",
        "source": "SGS third-party audit report #22-NV",
        "retracted": false,
        "retracted_reason": null
      },
      {
        "id": "78c47c87-ba09-48e2-9b7d-75ad39f615d9",
        "kind": "derived",
        "claim": "Northvale Dairy Co-op is a supplier in good standing.",
        "source": "rescind-agent: derived from supplier audit",
        "retracted": false,
        "retracted_reason": null
      },
      {
        "id": "39299127-b3e8-4630-a2ed-38455100dbb4",
        "kind": "derived",
        "claim": "Lot LOT-2026-0619-NV meets microbiological release criteria.",
        "source": "rescind-agent: derived from CoA #4471 and cold chain telemetry",
        "retracted": false,
        "retracted_reason": null
      },
      {
        "id": "bc9b5035-56b5-4ca9-a1cc-94aa8507ad9b",
        "kind": "derived",
        "claim": "Lot LOT-2026-0619-NV is cleared for release to Meridian Foods DC-7.",
        "source": "rescind-agent: derived from release criteria and supplier standing",
        "retracted": false,
        "retracted_reason": null
      }
    ],
    "decision": {
      "id": "516fd45f-e461-4306-88ff-a3bb9db297e2",
      "question": "May we release lot LOT-2026-0619-NV to Meridian Foods DC-7?",
      "verdict": "release",
      "rationale": "Offline reasoning: every supporting record for this lot reports a passing result and none reports a recall or contamination finding.",
      "decided_hlc": "1786975566676378348.0000000000",
      "model_id": "offline-deterministic",
      "offline_mode": true,
      "supporting": [
        {
          "id": "bc9b5035-56b5-4ca9-a1cc-94aa8507ad9b",
          "claim": "Lot LOT-2026-0619-NV is cleared for release to Meridian Foods DC-7.",
          "source": "rescind-agent: derived from release criteria and supplier standing",
          "distance": 0.201
        },
        {
          "id": "39299127-b3e8-4630-a2ed-38455100dbb4",
          "claim": "Lot LOT-2026-0619-NV meets microbiological release criteria.",
          "source": "rescind-agent: derived from CoA #4471 and cold chain telemetry",
          "distance": 0.242
        },
        {
          "id": "70ff044d-44fa-43dc-9ae7-4d32a4d5251a",
          "claim": "Cold chain log for pallet NV-8841 held 2.1-6.8 C across the full 41-hour transit with no excursions, within specification throughout.",
          "source": "Carrier telemetry, sensor #NV-9134",
          "distance": 0.3141
        },
        {
          "id": "824344d5-b477-4e4a-8580-1ec3e819b7f2",
          "claim": "Certificate of Analysis for lot LOT-2026-0619-NV: Cronobacter sakazakii not detected in 30 of 30 sampled tins; lot passed release testing.",
          "source": "Northvale Dairy Co-op QA, CoA #4471, issued 2026-06-24",
          "distance": 0.3141
        }
      ]
    },
    "retrieval_plan": "distribution: local\nvectorized: true\n\n\u2022 top-k\n\u2502 order: +column16\n\u2502 k: 5\n\u2502\n\u2514\u2500\u2500 \u2022 render\n    \u2502\n    \u2514\u2500\u2500 \u2022 lookup join\n        \u2502 table: facts@facts_pkey\n        \u2502 equality: (id) = (id)\n        \u2502 equality cols are key\n        \u2502\n        \u2514\u2500\u2500 \u2022 vector search\n              table: facts@facts_live_by_lot\n              target count: 5\n              prefix spans: [/'LOT-2026-0619-NV'/false - /'LOT-2026-0619-NV'/false]\n\nindex recommendations: 1\n1. type: index creation\n   SQL command: CREATE INDEX ON rescind.public.facts (lot_id) STORING (claim, embedding, retracted);"
  },
  "retraction": {
    "retraction_id": "090e6949-f52c-499e-b30b-de3fb2bb1663",
    "reason": "FDA Class II recall notice: Cronobacter sakazakii detected in a retained sample from the same production run. CoA #4471 withdrawn by Northvale QA.",
    "actor": "d.radrigan",
    "root_fact_ids": [
      "824344d5-b477-4e4a-8580-1ec3e819b7f2"
    ],
    "retracted_fact_ids": [
      "39299127-b3e8-4630-a2ed-38455100dbb4",
      "824344d5-b477-4e4a-8580-1ec3e819b7f2",
      "bc9b5035-56b5-4ca9-a1cc-94aa8507ad9b"
    ],
    "facts_retracted": 3,
    "cascade_beyond_roots": 2,
    "decisions_flagged": 1,
    "retracted_hlc": "1786975566684527594.0000000000"
  },
  "after": {
    "facts": [
      {
        "id": "824344d5-b477-4e4a-8580-1ec3e819b7f2",
        "kind": "observation",
        "claim": "Certificate of Analysis for lot LOT-2026-0619-NV: Cronobacter sakazakii not detected in 30 of 30 sampled tins; lot passed release testing.",
        "source": "Northvale Dairy Co-op QA, CoA #4471, issued 2026-06-24",
        "retracted": true,
        "retracted_reason": "FDA Class II recall notice: Cronobacter sakazakii detected in a retained sample from the same production run. CoA #4471 withdrawn by Northvale QA."
      },
      {
        "id": "70ff044d-44fa-43dc-9ae7-4d32a4d5251a",
        "kind": "observation",
        "claim": "Cold chain log for pallet NV-8841 held 2.1-6.8 C across the full 41-hour transit with no excursions, within specification throughout.",
        "source": "Carrier telemetry, sensor #NV-9134",
        "retracted": false,
        "retracted_reason": null
      },
      {
        "id": "54cf6ded-fddc-4068-abeb-7b0017f3821d",
        "kind": "observation",
        "claim": "Supplier audit of Northvale Dairy Co-op closed 2026-05-14 with no major findings.",
        "source": "SGS third-party audit report #22-NV",
        "retracted": false,
        "retracted_reason": null
      },
      {
        "id": "78c47c87-ba09-48e2-9b7d-75ad39f615d9",
        "kind": "derived",
        "claim": "Northvale Dairy Co-op is a supplier in good standing.",
        "source": "rescind-agent: derived from supplier audit",
        "retracted": false,
        "retracted_reason": null
      },
      {
        "id": "39299127-b3e8-4630-a2ed-38455100dbb4",
        "kind": "derived",
        "claim": "Lot LOT-2026-0619-NV meets microbiological release criteria.",
        "source": "rescind-agent: derived from CoA #4471 and cold chain telemetry",
        "retracted": true,
        "retracted_reason": "FDA Class II recall notice: Cronobacter sakazakii detected in a retained sample from the same production run. CoA #4471 withdrawn by Northvale QA."
      },
      {
        "id": "bc9b5035-56b5-4ca9-a1cc-94aa8507ad9b",
        "kind": "derived",
        "claim": "Lot LOT-2026-0619-NV is cleared for release to Meridian Foods DC-7.",
        "source": "rescind-agent: derived from release criteria and supplier standing",
        "retracted": true,
        "retracted_reason": "FDA Class II recall notice: Cronobacter sakazakii detected in a retained sample from the same production run. CoA #4471 withdrawn by Northvale QA."
      }
    ],
    "decision": {
      "id": "23f12cae-31b3-4b3c-b037-00dd5a26dbce",
      "question": "May we release lot LOT-2026-0619-NV to Meridian Foods DC-7?",
      "verdict": "refused",
      "rationale": "Refused: 1 live supporting record(s) within distance 0.55 for this lot, but 2 are required. Rescind will not answer from insufficient memory. Absence of evidence is not evidence of safety -- this lot is not cleared.",
      "decided_hlc": "1786975566693822791.0000000000",
      "model_id": "none-refused-before-model-call",
      "offline_mode": false,
      "supporting": [
        {
          "id": "70ff044d-44fa-43dc-9ae7-4d32a4d5251a",
          "claim": "Cold chain log for pallet NV-8841 held 2.1-6.8 C across the full 41-hour transit with no excursions, within specification throughout.",
          "source": "Carrier telemetry, sensor #NV-9134",
          "distance": 0.3141
        }
      ]
    },
    "open_reviews": [
      {
        "id": "516fd45f-e461-4306-88ff-a3bb9db297e2",
        "lot_id": "LOT-2026-0619-NV",
        "question": "May we release lot LOT-2026-0619-NV to Meridian Foods DC-7?",
        "verdict": "release",
        "rationale": "Offline reasoning: every supporting record for this lot reports a passing result and none reports a recall or contamination finding.",
        "review_reason": "supporting memory retracted: FDA Class II recall notice: Cronobacter sakazakii detected in a retained sample from the same production run. CoA #4471 withdrawn by Northvale QA.",
        "decided_at": "2026-08-17 14:06:06.676362+00:00"
      }
    ]
  },
  "replay": {
    "decided_hlc": "1786975566676378348.0000000000",
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
      "parent": "70ff044d-44fa-43dc-9ae7-4d32a4d5251a",
      "child": "39299127-b3e8-4630-a2ed-38455100dbb4"
    },
    {
      "parent": "824344d5-b477-4e4a-8580-1ec3e819b7f2",
      "child": "39299127-b3e8-4630-a2ed-38455100dbb4"
    },
    {
      "parent": "54cf6ded-fddc-4068-abeb-7b0017f3821d",
      "child": "78c47c87-ba09-48e2-9b7d-75ad39f615d9"
    },
    {
      "parent": "39299127-b3e8-4630-a2ed-38455100dbb4",
      "child": "bc9b5035-56b5-4ca9-a1cc-94aa8507ad9b"
    },
    {
      "parent": "78c47c87-ba09-48e2-9b7d-75ad39f615d9",
      "child": "bc9b5035-56b5-4ca9-a1cc-94aa8507ad9b"
    }
  ]
};
