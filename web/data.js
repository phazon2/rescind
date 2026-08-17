window.RESCIND_DATA = {
  "recorded_from": {
    "note": "Every value on this page was produced by scripts/record_demo.py running against a real CockroachDB cluster in CI. Nothing here is illustrative.",
    "cockroachdb_version": "CockroachDB CCL v25.3.0 (x86_64-pc-linux-gnu, built 2025/08/14 18:25:15, go1.23.7 X:nocoverageredesign)",
    "commit": "47aadd60fcfe089c69d957e27537b1c5ba355021",
    "run_url": "https://github.com/phazon2/rescind/actions/runs/32037703326",
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
        "id": "d75d2b86-d180-4011-8c6e-e6e8e74d8a41",
        "kind": "observation",
        "claim": "Certificate of Analysis for lot LOT-2026-0619-NV: Cronobacter sakazakii not detected in 30 of 30 sampled tins; lot passed release testing.",
        "source": "Northvale Dairy Co-op QA, CoA #4471, issued 2026-06-24",
        "retracted": false,
        "retracted_reason": null
      },
      {
        "id": "0830eda7-a2d4-4c8e-a6cf-c7e5c85d7de7",
        "kind": "observation",
        "claim": "Cold chain log for pallet NV-8841 held 2.1-6.8 C across the full 41-hour transit with no excursions, within specification throughout.",
        "source": "Carrier telemetry, sensor #NV-9134",
        "retracted": false,
        "retracted_reason": null
      },
      {
        "id": "038cf8d6-8d6a-4d4b-b66c-d1be9c0b2ab9",
        "kind": "observation",
        "claim": "Supplier audit of Northvale Dairy Co-op closed 2026-05-14 with no major findings.",
        "source": "SGS third-party audit report #22-NV",
        "retracted": false,
        "retracted_reason": null
      },
      {
        "id": "1360ba13-133f-45e1-9d8c-fa622d2f37e3",
        "kind": "derived",
        "claim": "Northvale Dairy Co-op is a supplier in good standing.",
        "source": "rescind-agent: derived from supplier audit",
        "retracted": false,
        "retracted_reason": null
      },
      {
        "id": "c00c4a8e-ace6-4e3f-bb62-049e934a8636",
        "kind": "derived",
        "claim": "Lot LOT-2026-0619-NV meets microbiological release criteria.",
        "source": "rescind-agent: derived from CoA #4471 and cold chain telemetry",
        "retracted": false,
        "retracted_reason": null
      },
      {
        "id": "6d2a0163-8b61-41e4-9c49-e4e4686cc4f2",
        "kind": "derived",
        "claim": "Lot LOT-2026-0619-NV is cleared for release to Meridian Foods DC-7.",
        "source": "rescind-agent: derived from release criteria and supplier standing",
        "retracted": false,
        "retracted_reason": null
      }
    ],
    "decision": {
      "id": "a94f185d-55fc-4595-b152-acf3ba5ae450",
      "question": "May we release lot LOT-2026-0619-NV to Meridian Foods DC-7?",
      "verdict": "release",
      "rationale": "Offline reasoning: every supporting record for this lot reports a passing result and none reports a recall or contamination finding.",
      "decided_hlc": "1786975468946346745.0000000000",
      "model_id": "offline-deterministic",
      "offline_mode": true,
      "supporting": [
        {
          "id": "6d2a0163-8b61-41e4-9c49-e4e4686cc4f2",
          "claim": "Lot LOT-2026-0619-NV is cleared for release to Meridian Foods DC-7.",
          "source": "rescind-agent: derived from release criteria and supplier standing",
          "distance": 0.201
        },
        {
          "id": "c00c4a8e-ace6-4e3f-bb62-049e934a8636",
          "claim": "Lot LOT-2026-0619-NV meets microbiological release criteria.",
          "source": "rescind-agent: derived from CoA #4471 and cold chain telemetry",
          "distance": 0.242
        },
        {
          "id": "d75d2b86-d180-4011-8c6e-e6e8e74d8a41",
          "claim": "Certificate of Analysis for lot LOT-2026-0619-NV: Cronobacter sakazakii not detected in 30 of 30 sampled tins; lot passed release testing.",
          "source": "Northvale Dairy Co-op QA, CoA #4471, issued 2026-06-24",
          "distance": 0.3141
        },
        {
          "id": "0830eda7-a2d4-4c8e-a6cf-c7e5c85d7de7",
          "claim": "Cold chain log for pallet NV-8841 held 2.1-6.8 C across the full 41-hour transit with no excursions, within specification throughout.",
          "source": "Carrier telemetry, sensor #NV-9134",
          "distance": 0.3141
        }
      ]
    },
    "retrieval_plan": "distribution: local\nvectorized: true\n\n\u2022 top-k\n\u2502 order: +column16\n\u2502 k: 5\n\u2502\n\u2514\u2500\u2500 \u2022 render\n    \u2502\n    \u2514\u2500\u2500 \u2022 lookup join\n        \u2502 table: facts@facts_pkey\n        \u2502 equality: (id) = (id)\n        \u2502 equality cols are key\n        \u2502\n        \u2514\u2500\u2500 \u2022 vector search\n              table: facts@facts_live_by_lot\n              target count: 5\n              prefix spans: [/'LOT-2026-0619-NV'/false - /'LOT-2026-0619-NV'/false]\n\nindex recommendations: 1\n1. type: index creation\n   SQL command: CREATE INDEX ON rescind.public.facts (lot_id) STORING (claim, embedding, retracted);"
  },
  "retraction": {
    "retraction_id": "290e5238-a2fd-45f5-a254-a838d99c1639",
    "reason": "FDA Class II recall notice: Cronobacter sakazakii detected in a retained sample from the same production run. CoA #4471 withdrawn by Northvale QA.",
    "actor": "d.radrigan",
    "root_fact_ids": [
      "d75d2b86-d180-4011-8c6e-e6e8e74d8a41"
    ],
    "retracted_fact_ids": [
      "6d2a0163-8b61-41e4-9c49-e4e4686cc4f2",
      "c00c4a8e-ace6-4e3f-bb62-049e934a8636",
      "d75d2b86-d180-4011-8c6e-e6e8e74d8a41"
    ],
    "facts_retracted": 3,
    "cascade_beyond_roots": 2,
    "decisions_flagged": 1,
    "retracted_hlc": "1786975468955578783.0000000000"
  },
  "after": {
    "facts": [
      {
        "id": "d75d2b86-d180-4011-8c6e-e6e8e74d8a41",
        "kind": "observation",
        "claim": "Certificate of Analysis for lot LOT-2026-0619-NV: Cronobacter sakazakii not detected in 30 of 30 sampled tins; lot passed release testing.",
        "source": "Northvale Dairy Co-op QA, CoA #4471, issued 2026-06-24",
        "retracted": true,
        "retracted_reason": "FDA Class II recall notice: Cronobacter sakazakii detected in a retained sample from the same production run. CoA #4471 withdrawn by Northvale QA."
      },
      {
        "id": "0830eda7-a2d4-4c8e-a6cf-c7e5c85d7de7",
        "kind": "observation",
        "claim": "Cold chain log for pallet NV-8841 held 2.1-6.8 C across the full 41-hour transit with no excursions, within specification throughout.",
        "source": "Carrier telemetry, sensor #NV-9134",
        "retracted": false,
        "retracted_reason": null
      },
      {
        "id": "038cf8d6-8d6a-4d4b-b66c-d1be9c0b2ab9",
        "kind": "observation",
        "claim": "Supplier audit of Northvale Dairy Co-op closed 2026-05-14 with no major findings.",
        "source": "SGS third-party audit report #22-NV",
        "retracted": false,
        "retracted_reason": null
      },
      {
        "id": "1360ba13-133f-45e1-9d8c-fa622d2f37e3",
        "kind": "derived",
        "claim": "Northvale Dairy Co-op is a supplier in good standing.",
        "source": "rescind-agent: derived from supplier audit",
        "retracted": false,
        "retracted_reason": null
      },
      {
        "id": "c00c4a8e-ace6-4e3f-bb62-049e934a8636",
        "kind": "derived",
        "claim": "Lot LOT-2026-0619-NV meets microbiological release criteria.",
        "source": "rescind-agent: derived from CoA #4471 and cold chain telemetry",
        "retracted": true,
        "retracted_reason": "FDA Class II recall notice: Cronobacter sakazakii detected in a retained sample from the same production run. CoA #4471 withdrawn by Northvale QA."
      },
      {
        "id": "6d2a0163-8b61-41e4-9c49-e4e4686cc4f2",
        "kind": "derived",
        "claim": "Lot LOT-2026-0619-NV is cleared for release to Meridian Foods DC-7.",
        "source": "rescind-agent: derived from release criteria and supplier standing",
        "retracted": true,
        "retracted_reason": "FDA Class II recall notice: Cronobacter sakazakii detected in a retained sample from the same production run. CoA #4471 withdrawn by Northvale QA."
      }
    ],
    "decision": {
      "id": "7bf4adba-5d0e-4d59-8db9-0c41a576db7d",
      "question": "May we release lot LOT-2026-0619-NV to Meridian Foods DC-7?",
      "verdict": "refused",
      "rationale": "Refused: 1 live supporting record(s) within distance 0.55 for this lot, but 2 are required. Rescind will not answer from insufficient memory. Absence of evidence is not evidence of safety -- this lot is not cleared.",
      "decided_hlc": "1786975468966247097.0000000000",
      "model_id": "none-refused-before-model-call",
      "offline_mode": false,
      "supporting": [
        {
          "id": "0830eda7-a2d4-4c8e-a6cf-c7e5c85d7de7",
          "claim": "Cold chain log for pallet NV-8841 held 2.1-6.8 C across the full 41-hour transit with no excursions, within specification throughout.",
          "source": "Carrier telemetry, sensor #NV-9134",
          "distance": 0.3141
        }
      ]
    },
    "open_reviews": [
      {
        "id": "a94f185d-55fc-4595-b152-acf3ba5ae450",
        "lot_id": "LOT-2026-0619-NV",
        "question": "May we release lot LOT-2026-0619-NV to Meridian Foods DC-7?",
        "verdict": "release",
        "rationale": "Offline reasoning: every supporting record for this lot reports a passing result and none reports a recall or contamination finding.",
        "review_reason": "supporting memory retracted: FDA Class II recall notice: Cronobacter sakazakii detected in a retained sample from the same production run. CoA #4471 withdrawn by Northvale QA.",
        "decided_at": "2026-08-17 14:04:28.946332+00:00"
      }
    ]
  },
  "replay": {
    "decided_hlc": "1786975468946346745.0000000000",
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
      "parent": "038cf8d6-8d6a-4d4b-b66c-d1be9c0b2ab9",
      "child": "1360ba13-133f-45e1-9d8c-fa622d2f37e3"
    },
    {
      "parent": "1360ba13-133f-45e1-9d8c-fa622d2f37e3",
      "child": "6d2a0163-8b61-41e4-9c49-e4e4686cc4f2"
    },
    {
      "parent": "c00c4a8e-ace6-4e3f-bb62-049e934a8636",
      "child": "6d2a0163-8b61-41e4-9c49-e4e4686cc4f2"
    },
    {
      "parent": "0830eda7-a2d4-4c8e-a6cf-c7e5c85d7de7",
      "child": "c00c4a8e-ace6-4e3f-bb62-049e934a8636"
    },
    {
      "parent": "d75d2b86-d180-4011-8c6e-e6e8e74d8a41",
      "child": "c00c4a8e-ace6-4e3f-bb62-049e934a8636"
    }
  ]
};
