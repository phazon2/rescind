#!/usr/bin/env python3
"""Build ci/latest.json -- a machine-readable receipt for the last verified run.

Judges are not required to run the code. This file is how the repository proves
the test suite actually executed against a real CockroachDB cluster, which
cluster version it was, and which of the design's load-bearing assumptions were
observed to hold.

It records what a RUN OBSERVED. What each test CERTIFIES is stated in the test
docstrings; the two are different claims and are kept separate on purpose.
"""

from __future__ import annotations

import json
import os
import pathlib
import sys
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent
CI = ROOT / "ci"


def main() -> int:
    junit = CI / "junit.xml"
    if not junit.exists():
        print(f"missing {junit}", file=sys.stderr)
        return 1

    root = ET.parse(junit).getroot()
    suite = root.find("testsuite") if root.tag == "testsuites" else root

    cases = []
    for case in suite.iter("testcase"):
        status = "passed"
        message = None
        for tag, label in (("failure", "failed"), ("error", "error"), ("skipped", "skipped")):
            found = case.find(tag)
            if found is not None:
                status = label
                message = (found.get("message") or "").strip()[:400]
                break
        cases.append(
            {
                "test": case.get("name"),
                "certifies": (case.findtext("properties/property[@name='doc']") or "").strip()
                or None,
                "status": status,
                "seconds": round(float(case.get("time", 0.0)), 3),
                "message": message,
            }
        )

    probe_path = CI / "probe.json"
    probe = json.loads(probe_path.read_text()) if probe_path.exists() else {}

    receipt = {
        "what_this_is": (
            "Machine-readable receipt for the most recent verification run. "
            "Records what this run observed, not what the tests claim."
        ),
        "commit": os.environ.get("GITHUB_SHA", "unknown"),
        "ref": os.environ.get("GITHUB_REF_NAME", "unknown"),
        "run_url": (
            f"{os.environ.get('GITHUB_SERVER_URL', 'https://github.com')}/"
            f"{os.environ.get('GITHUB_REPOSITORY', '')}/actions/runs/"
            f"{os.environ.get('GITHUB_RUN_ID', '')}"
        ),
        "generated_at_utc": os.environ.get("RESCIND_RUN_TIMESTAMP", "unknown"),
        "cockroachdb": {
            "version": probe.get("cluster", "unknown"),
            "topology": "single-node, in-memory store, started on the CI runner",
        },
        "bedrock": {
            "mode": "offline-deterministic"
            if os.environ.get("RESCIND_OFFLINE", "").lower() in {"1", "true", "yes"}
            else "live",
            "note": (
                "CI has no AWS credentials, so embeddings and reasoning use the "
                "deterministic stand-in. The database behaviour under test is "
                "unaffected: tests supply their own controlled vectors."
            ),
        },
        "tests": {
            "total": len(cases),
            "passed": sum(1 for c in cases if c["status"] == "passed"),
            "failed": sum(1 for c in cases if c["status"] in {"failed", "error"}),
            "skipped": sum(1 for c in cases if c["status"] == "skipped"),
            "cases": cases,
        },
        "probes": probe.get("probes", []),
    }

    CI.mkdir(exist_ok=True)
    (CI / "latest.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(
        f"ci/latest.json: {receipt['tests']['passed']}/{receipt['tests']['total']} passed "
        f"against {receipt['cockroachdb']['version']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
