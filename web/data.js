window.RESCIND_DATA = {
  "recorded_from": {
    "note": "Every value on this page was produced by scripts/record_demo.py running against a real CockroachDB cluster in CI. Nothing here is illustrative.",
    "cockroachdb_version": "CockroachDB CCL v25.3.0 (x86_64-pc-linux-gnu, built 2025/08/14 18:25:15, go1.23.7 X:nocoverageredesign)",
    "commit": "76ea8d60d55abbb5d6eb2ee7e517d39fca6f289e",
    "run_url": "https://github.com/phazon2/rescind/actions/runs/32038010760",
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
        "id": "e847d67a-631d-46be-8208-b69e4e4e93e1",
        "kind": "observation",
        "claim": "Certificate of Analysis for lot LOT-2026-0619-NV: Cronobacter sakazakii not detected in 30 of 30 sampled tins; lot passed release testing.",
        "source": "Northvale Dairy Co-op QA, CoA #4471, issued 2026-06-24",
        "retracted": false,
        "retracted_reason": null
      },
      {
        "id": "855c8974-91e6-4699-9d11-c70ad6f6680e",
        "kind": "observation",
        "claim": "Cold chain log for pallet NV-8841 held 2.1-6.8 C across the full 41-hour transit with no excursions, within specification throughout.",
        "source": "Carrier telemetry, sensor #NV-9134",
        "retracted": false,
        "retracted_reason": null
      },
      {
        "id": "faa694cd-a3bd-47af-920e-48ac4e38b597",
        "kind": "observation",
        "claim": "Supplier audit of Northvale Dairy Co-op closed 2026-05-14 with no major findings.",
        "source": "SGS third-party audit report #22-NV",
        "retracted": false,
        "retracted_reason": null
      },
      {
        "id": "65fb9a85-4152-42f4-ad92-63f1e280d4df",
        "kind": "derived",
        "claim": "Northvale Dairy Co-op is a supplier in good standing.",
        "source": "rescind-agent: derived from supplier audit",
        "retracted": false,
        "retracted_reason": null
      },
      {
        "id": "a73218ca-cc64-45df-ad0f-6750ec951b69",
        "kind": "derived",
        "claim": "Lot LOT-2026-0619-NV meets microbiological release criteria.",
        "source": "rescind-agent: derived from CoA #4471 and cold chain telemetry",
        "retracted": false,
        "retracted_reason": null
      },
      {
        "id": "c55e4661-72a7-47cc-8cf6-456c53bbe3ff",
        "kind": "derived",
        "claim": "Lot LOT-2026-0619-NV is cleared for release to Meridian Foods DC-7.",
        "source": "rescind-agent: derived from release criteria and supplier standing",
        "retracted": false,
        "retracted_reason": null
      }
    ],
    "decision": {
      "id": "b725ec5c-924e-4756-9441-f7fd97146d3c",
      "question": "May we release lot LOT-2026-0619-NV to Meridian Foods DC-7?",
      "verdict": "release",
      "rationale": "Offline reasoning: every supporting record for this lot reports a passing result and none reports a recall or contamination finding.",
      "decided_hlc": "1786975758636711156.0000000000",
      "model_id": "offline-deterministic",
      "offline_mode": true,
      "supporting": [
        {
          "id": "c55e4661-72a7-47cc-8cf6-456c53bbe3ff",
          "claim": "Lot LOT-2026-0619-NV is cleared for release to Meridian Foods DC-7.",
          "source": "rescind-agent: derived from release criteria and supplier standing",
          "distance": 0.201
        },
        {
          "id": "a73218ca-cc64-45df-ad0f-6750ec951b69",
          "claim": "Lot LOT-2026-0619-NV meets microbiological release criteria.",
          "source": "rescind-agent: derived from CoA #4471 and cold chain telemetry",
          "distance": 0.242
        },
        {
          "id": "855c8974-91e6-4699-9d11-c70ad6f6680e",
          "claim": "Cold chain log for pallet NV-8841 held 2.1-6.8 C across the full 41-hour transit with no excursions, within specification throughout.",
          "source": "Carrier telemetry, sensor #NV-9134",
          "distance": 0.3141
        },
        {
          "id": "e847d67a-631d-46be-8208-b69e4e4e93e1",
          "claim": "Certificate of Analysis for lot LOT-2026-0619-NV: Cronobacter sakazakii not detected in 30 of 30 sampled tins; lot passed release testing.",
          "source": "Northvale Dairy Co-op QA, CoA #4471, issued 2026-06-24",
          "distance": 0.3141
        }
      ]
    },
    "retrieval_plan": "distribution: local\nvectorized: true\n\n\u2022 top-k\n\u2502 order: +column16\n\u2502 k: 5\n\u2502\n\u2514\u2500\u2500 \u2022 render\n    \u2502\n    \u2514\u2500\u2500 \u2022 lookup join\n        \u2502 table: facts@facts_pkey\n        \u2502 equality: (id) = (id)\n        \u2502 equality cols are key\n        \u2502\n        \u2514\u2500\u2500 \u2022 vector search\n              table: facts@facts_live_by_lot\n              target count: 5\n              prefix spans: [/'LOT-2026-0619-NV'/false - /'LOT-2026-0619-NV'/false]\n\nindex recommendations: 1\n1. type: index creation\n   SQL command: CREATE INDEX ON rescind.public.facts (lot_id) STORING (claim, embedding, retracted);"
  },
  "retraction": {
    "retraction_id": "d6d7f84a-5f91-4f4e-8a7e-fc8e3e5a59c9",
    "reason": "FDA Class II recall notice: Cronobacter sakazakii detected in a retained sample from the same production run. CoA #4471 withdrawn by Northvale QA.",
    "actor": "d.radrigan",
    "root_fact_ids": [
      "e847d67a-631d-46be-8208-b69e4e4e93e1"
    ],
    "retracted_fact_ids": [
      "a73218ca-cc64-45df-ad0f-6750ec951b69",
      "c55e4661-72a7-47cc-8cf6-456c53bbe3ff",
      "e847d67a-631d-46be-8208-b69e4e4e93e1"
    ],
    "facts_retracted": 3,
    "cascade_beyond_roots": 2,
    "decisions_flagged": 1,
    "retracted_hlc": "1786975758645761990.0000000000"
  },
  "after": {
    "facts": [
      {
        "id": "e847d67a-631d-46be-8208-b69e4e4e93e1",
        "kind": "observation",
        "claim": "Certificate of Analysis for lot LOT-2026-0619-NV: Cronobacter sakazakii not detected in 30 of 30 sampled tins; lot passed release testing.",
        "source": "Northvale Dairy Co-op QA, CoA #4471, issued 2026-06-24",
        "retracted": true,
        "retracted_reason": "FDA Class II recall notice: Cronobacter sakazakii detected in a retained sample from the same production run. CoA #4471 withdrawn by Northvale QA."
      },
      {
        "id": "855c8974-91e6-4699-9d11-c70ad6f6680e",
        "kind": "observation",
        "claim": "Cold chain log for pallet NV-8841 held 2.1-6.8 C across the full 41-hour transit with no excursions, within specification throughout.",
        "source": "Carrier telemetry, sensor #NV-9134",
        "retracted": false,
        "retracted_reason": null
      },
      {
        "id": "faa694cd-a3bd-47af-920e-48ac4e38b597",
        "kind": "observation",
        "claim": "Supplier audit of Northvale Dairy Co-op closed 2026-05-14 with no major findings.",
        "source": "SGS third-party audit report #22-NV",
        "retracted": false,
        "retracted_reason": null
      },
      {
        "id": "65fb9a85-4152-42f4-ad92-63f1e280d4df",
        "kind": "derived",
        "claim": "Northvale Dairy Co-op is a supplier in good standing.",
        "source": "rescind-agent: derived from supplier audit",
        "retracted": false,
        "retracted_reason": null
      },
      {
        "id": "a73218ca-cc64-45df-ad0f-6750ec951b69",
        "kind": "derived",
        "claim": "Lot LOT-2026-0619-NV meets microbiological release criteria.",
        "source": "rescind-agent: derived from CoA #4471 and cold chain telemetry",
        "retracted": true,
        "retracted_reason": "FDA Class II recall notice: Cronobacter sakazakii detected in a retained sample from the same production run. CoA #4471 withdrawn by Northvale QA."
      },
      {
        "id": "c55e4661-72a7-47cc-8cf6-456c53bbe3ff",
        "kind": "derived",
        "claim": "Lot LOT-2026-0619-NV is cleared for release to Meridian Foods DC-7.",
        "source": "rescind-agent: derived from release criteria and supplier standing",
        "retracted": true,
        "retracted_reason": "FDA Class II recall notice: Cronobacter sakazakii detected in a retained sample from the same production run. CoA #4471 withdrawn by Northvale QA."
      }
    ],
    "decision": {
      "id": "a8dd88ef-de36-4c85-b163-1209399462c6",
      "question": "May we release lot LOT-2026-0619-NV to Meridian Foods DC-7?",
      "verdict": "refused",
      "rationale": "Refused: 1 live supporting record(s) within distance 0.55 for this lot, but 2 are required. Rescind will not answer from insufficient memory. Absence of evidence is not evidence of safety -- this lot is not cleared.",
      "decided_hlc": "1786975758656657424.0000000000",
      "model_id": "none-refused-before-model-call",
      "offline_mode": false,
      "supporting": [
        {
          "id": "855c8974-91e6-4699-9d11-c70ad6f6680e",
          "claim": "Cold chain log for pallet NV-8841 held 2.1-6.8 C across the full 41-hour transit with no excursions, within specification throughout.",
          "source": "Carrier telemetry, sensor #NV-9134",
          "distance": 0.3141
        }
      ]
    },
    "open_reviews": [
      {
        "id": "b725ec5c-924e-4756-9441-f7fd97146d3c",
        "lot_id": "LOT-2026-0619-NV",
        "question": "May we release lot LOT-2026-0619-NV to Meridian Foods DC-7?",
        "verdict": "release",
        "rationale": "Offline reasoning: every supporting record for this lot reports a passing result and none reports a recall or contamination finding.",
        "review_reason": "supporting memory retracted: FDA Class II recall notice: Cronobacter sakazakii detected in a retained sample from the same production run. CoA #4471 withdrawn by Northvale QA.",
        "decided_at": "2026-08-17 14:09:18.636673+00:00"
      }
    ]
  },
  "replay": {
    "decided_hlc": "1786975758636711156.0000000000",
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
      "parent": "faa694cd-a3bd-47af-920e-48ac4e38b597",
      "child": "65fb9a85-4152-42f4-ad92-63f1e280d4df"
    },
    {
      "parent": "855c8974-91e6-4699-9d11-c70ad6f6680e",
      "child": "a73218ca-cc64-45df-ad0f-6750ec951b69"
    },
    {
      "parent": "e847d67a-631d-46be-8208-b69e4e4e93e1",
      "child": "a73218ca-cc64-45df-ad0f-6750ec951b69"
    },
    {
      "parent": "65fb9a85-4152-42f4-ad92-63f1e280d4df",
      "child": "c55e4661-72a7-47cc-8cf6-456c53bbe3ff"
    },
    {
      "parent": "a73218ca-cc64-45df-ad0f-6750ec951b69",
      "child": "c55e4661-72a7-47cc-8cf6-456c53bbe3ff"
    }
  ]
};
