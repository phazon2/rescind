window.RESCIND_DATA = {
  "recorded_from": {
    "note": "Every value on this page was produced by scripts/record_demo.py running against a real CockroachDB cluster in CI. Nothing here is illustrative.",
    "cockroachdb_version": "CockroachDB CCL v25.3.0 (x86_64-pc-linux-gnu, built 2025/08/14 18:25:15, go1.23.7 X:nocoverageredesign)",
    "commit": "e75d5017b0ee55e4d01f4b138b568c65c42daf05",
    "run_url": "https://github.com/phazon2/rescind/actions/runs/32082992721",
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
        "id": "8a3a0992-e6ab-4e47-b43d-94a23b47ec3c",
        "kind": "observation",
        "claim": "Certificate of Analysis for lot LOT-2026-0619-NV: Cronobacter sakazakii not detected in 30 of 30 sampled tins; lot passed release testing.",
        "source": "Northvale Dairy Co-op QA, CoA #4471, issued 2026-06-24",
        "retracted": false,
        "retracted_reason": null
      },
      {
        "id": "08c19f1b-8327-49ba-8866-5c978f4ecedb",
        "kind": "observation",
        "claim": "Cold chain log for pallet NV-8841 held 2.1-6.8 C across the full 41-hour transit with no excursions, within specification throughout.",
        "source": "Carrier telemetry, sensor #NV-9134",
        "retracted": false,
        "retracted_reason": null
      },
      {
        "id": "cd640b9a-878d-4bc9-9afa-e6806f0d2b48",
        "kind": "observation",
        "claim": "Supplier audit of Northvale Dairy Co-op closed 2026-05-14 with no major findings.",
        "source": "SGS third-party audit report #22-NV",
        "retracted": false,
        "retracted_reason": null
      },
      {
        "id": "24981dd7-1761-4ca2-a699-27a9bc30047c",
        "kind": "derived",
        "claim": "Northvale Dairy Co-op is a supplier in good standing.",
        "source": "rescind-agent: derived from supplier audit",
        "retracted": false,
        "retracted_reason": null
      },
      {
        "id": "d994425a-8cc4-4bcb-aa79-a3ec34b01789",
        "kind": "derived",
        "claim": "Lot LOT-2026-0619-NV meets microbiological release criteria.",
        "source": "rescind-agent: derived from CoA #4471 and cold chain telemetry",
        "retracted": false,
        "retracted_reason": null
      },
      {
        "id": "2c5c9327-40ce-4349-aceb-edc4efb27648",
        "kind": "derived",
        "claim": "Lot LOT-2026-0619-NV is cleared for release to Meridian Foods DC-7.",
        "source": "rescind-agent: derived from release criteria and supplier standing",
        "retracted": false,
        "retracted_reason": null
      }
    ],
    "decision": {
      "id": "b28ec375-2267-4455-a161-8722d1373d43",
      "question": "May we release lot LOT-2026-0619-NV to Meridian Foods DC-7?",
      "verdict": "release",
      "rationale": "Offline reasoning: every supporting record for this lot reports a passing result and none reports a recall or contamination finding.",
      "decided_hlc": "1787011427424983869.0000000000",
      "model_id": "offline-deterministic",
      "offline_mode": true,
      "supporting": [
        {
          "id": "2c5c9327-40ce-4349-aceb-edc4efb27648",
          "claim": "Lot LOT-2026-0619-NV is cleared for release to Meridian Foods DC-7.",
          "source": "rescind-agent: derived from release criteria and supplier standing",
          "distance": 0.201
        },
        {
          "id": "d994425a-8cc4-4bcb-aa79-a3ec34b01789",
          "claim": "Lot LOT-2026-0619-NV meets microbiological release criteria.",
          "source": "rescind-agent: derived from CoA #4471 and cold chain telemetry",
          "distance": 0.242
        },
        {
          "id": "8a3a0992-e6ab-4e47-b43d-94a23b47ec3c",
          "claim": "Certificate of Analysis for lot LOT-2026-0619-NV: Cronobacter sakazakii not detected in 30 of 30 sampled tins; lot passed release testing.",
          "source": "Northvale Dairy Co-op QA, CoA #4471, issued 2026-06-24",
          "distance": 0.3141
        },
        {
          "id": "08c19f1b-8327-49ba-8866-5c978f4ecedb",
          "claim": "Cold chain log for pallet NV-8841 held 2.1-6.8 C across the full 41-hour transit with no excursions, within specification throughout.",
          "source": "Carrier telemetry, sensor #NV-9134",
          "distance": 0.3141
        }
      ]
    },
    "retrieval_plan": "distribution: local\nvectorized: true\n\n\u2022 top-k\n\u2502 order: +column16\n\u2502 k: 5\n\u2502\n\u2514\u2500\u2500 \u2022 render\n    \u2502\n    \u2514\u2500\u2500 \u2022 lookup join\n        \u2502 table: facts@facts_pkey\n        \u2502 equality: (id) = (id)\n        \u2502 equality cols are key\n        \u2502\n        \u2514\u2500\u2500 \u2022 vector search\n              table: facts@facts_live_by_lot\n              target count: 5\n              prefix spans: [/'LOT-2026-0619-NV'/false - /'LOT-2026-0619-NV'/false]\n\nindex recommendations: 1\n1. type: index creation\n   SQL command: CREATE INDEX ON rescind.public.facts (lot_id) STORING (claim, embedding, retracted);"
  },
  "retraction": {
    "retraction_id": "42fbe040-403d-445b-900f-b2f672dc9e68",
    "reason": "FDA Class II recall notice: Cronobacter sakazakii detected in a retained sample from the same production run. CoA #4471 withdrawn by Northvale QA.",
    "actor": "d.radrigan",
    "root_fact_ids": [
      "8a3a0992-e6ab-4e47-b43d-94a23b47ec3c"
    ],
    "retracted_fact_ids": [
      "2c5c9327-40ce-4349-aceb-edc4efb27648",
      "8a3a0992-e6ab-4e47-b43d-94a23b47ec3c",
      "d994425a-8cc4-4bcb-aa79-a3ec34b01789"
    ],
    "facts_retracted": 3,
    "cascade_beyond_roots": 2,
    "decisions_flagged": 1,
    "retracted_hlc": "1787011427434036418.0000000000"
  },
  "after": {
    "facts": [
      {
        "id": "8a3a0992-e6ab-4e47-b43d-94a23b47ec3c",
        "kind": "observation",
        "claim": "Certificate of Analysis for lot LOT-2026-0619-NV: Cronobacter sakazakii not detected in 30 of 30 sampled tins; lot passed release testing.",
        "source": "Northvale Dairy Co-op QA, CoA #4471, issued 2026-06-24",
        "retracted": true,
        "retracted_reason": "FDA Class II recall notice: Cronobacter sakazakii detected in a retained sample from the same production run. CoA #4471 withdrawn by Northvale QA."
      },
      {
        "id": "08c19f1b-8327-49ba-8866-5c978f4ecedb",
        "kind": "observation",
        "claim": "Cold chain log for pallet NV-8841 held 2.1-6.8 C across the full 41-hour transit with no excursions, within specification throughout.",
        "source": "Carrier telemetry, sensor #NV-9134",
        "retracted": false,
        "retracted_reason": null
      },
      {
        "id": "cd640b9a-878d-4bc9-9afa-e6806f0d2b48",
        "kind": "observation",
        "claim": "Supplier audit of Northvale Dairy Co-op closed 2026-05-14 with no major findings.",
        "source": "SGS third-party audit report #22-NV",
        "retracted": false,
        "retracted_reason": null
      },
      {
        "id": "24981dd7-1761-4ca2-a699-27a9bc30047c",
        "kind": "derived",
        "claim": "Northvale Dairy Co-op is a supplier in good standing.",
        "source": "rescind-agent: derived from supplier audit",
        "retracted": false,
        "retracted_reason": null
      },
      {
        "id": "d994425a-8cc4-4bcb-aa79-a3ec34b01789",
        "kind": "derived",
        "claim": "Lot LOT-2026-0619-NV meets microbiological release criteria.",
        "source": "rescind-agent: derived from CoA #4471 and cold chain telemetry",
        "retracted": true,
        "retracted_reason": "FDA Class II recall notice: Cronobacter sakazakii detected in a retained sample from the same production run. CoA #4471 withdrawn by Northvale QA."
      },
      {
        "id": "2c5c9327-40ce-4349-aceb-edc4efb27648",
        "kind": "derived",
        "claim": "Lot LOT-2026-0619-NV is cleared for release to Meridian Foods DC-7.",
        "source": "rescind-agent: derived from release criteria and supplier standing",
        "retracted": true,
        "retracted_reason": "FDA Class II recall notice: Cronobacter sakazakii detected in a retained sample from the same production run. CoA #4471 withdrawn by Northvale QA."
      }
    ],
    "decision": {
      "id": "bb6f42ce-6109-4aa8-90a8-4fcb43afb4e6",
      "question": "May we release lot LOT-2026-0619-NV to Meridian Foods DC-7?",
      "verdict": "refused",
      "rationale": "Refused: 1 live supporting record(s) within distance 0.55 for this lot, but 2 are required. Rescind will not answer from insufficient memory. Absence of evidence is not evidence of safety -- this lot is not cleared.",
      "decided_hlc": "1787011427443168017.0000000000",
      "model_id": "none-refused-before-model-call",
      "offline_mode": false,
      "supporting": [
        {
          "id": "08c19f1b-8327-49ba-8866-5c978f4ecedb",
          "claim": "Cold chain log for pallet NV-8841 held 2.1-6.8 C across the full 41-hour transit with no excursions, within specification throughout.",
          "source": "Carrier telemetry, sensor #NV-9134",
          "distance": 0.3141
        }
      ]
    },
    "open_reviews": [
      {
        "id": "b28ec375-2267-4455-a161-8722d1373d43",
        "lot_id": "LOT-2026-0619-NV",
        "question": "May we release lot LOT-2026-0619-NV to Meridian Foods DC-7?",
        "verdict": "release",
        "rationale": "Offline reasoning: every supporting record for this lot reports a passing result and none reports a recall or contamination finding.",
        "review_reason": "supporting memory retracted: FDA Class II recall notice: Cronobacter sakazakii detected in a retained sample from the same production run. CoA #4471 withdrawn by Northvale QA.",
        "decided_at": "2026-08-18 00:03:47.424965+00:00"
      }
    ]
  },
  "replay": {
    "decided_hlc": "1787011427424983869.0000000000",
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
      "parent": "cd640b9a-878d-4bc9-9afa-e6806f0d2b48",
      "child": "24981dd7-1761-4ca2-a699-27a9bc30047c"
    },
    {
      "parent": "24981dd7-1761-4ca2-a699-27a9bc30047c",
      "child": "2c5c9327-40ce-4349-aceb-edc4efb27648"
    },
    {
      "parent": "d994425a-8cc4-4bcb-aa79-a3ec34b01789",
      "child": "2c5c9327-40ce-4349-aceb-edc4efb27648"
    },
    {
      "parent": "08c19f1b-8327-49ba-8866-5c978f4ecedb",
      "child": "d994425a-8cc4-4bcb-aa79-a3ec34b01789"
    },
    {
      "parent": "8a3a0992-e6ab-4e47-b43d-94a23b47ec3c",
      "child": "d994425a-8cc4-4bcb-aa79-a3ec34b01789"
    }
  ]
};
