#!/usr/bin/env bash
#
# CockroachDB Cloud control-plane setup for Rescind, via the ccloud CLI.
#
# ============================================================================
# STATUS: NOT YET EXECUTED. Read this before believing anything below.
#
# The environment this repository was built in permitted outbound traffic on
# port 443 only. CockroachDB's SQL port (26257) was unreachable and
# binaries.cockroachdb.com was blocked by egress policy, so no CockroachDB Cloud
# cluster could be provisioned or reached, and the ccloud CLI could not be
# installed. Every claim this project makes is therefore verified against a
# single-node cluster started inside GitHub Actions instead -- see ci/latest.json.
#
# This script is the control-plane work, written out so it is one command away.
# When it is run, paste its output into ci/ccloud-evidence.txt and commit that,
# so the claim is backed by a receipt like everything else here. Until then the
# README lists ccloud as NOT exercised. See docs/LIMITS.md.
# ============================================================================
#
# Usage:
#   export CCLOUD_API_KEY=...        # from the CockroachDB Cloud console
#   bash scripts/ccloud_setup.sh
#
set -euo pipefail

CLUSTER_NAME="${CLUSTER_NAME:-rescind}"
CLOUD="${CLOUD:-aws}"
REGION="${REGION:-us-east-1}"
DB_NAME="rescind"

say() { printf '\n=== %s ===\n' "$1"; }

if ! command -v ccloud >/dev/null 2>&1; then
  echo "ccloud CLI not found. Install it with:"
  echo "  brew install cockroachdb/tap/ccloud     # macOS"
  echo "  curl https://binaries.cockroachdb.com/ccloud/ccloud_linux-amd64_latest.tar.gz | tar -xz"
  exit 1
fi

say "1. Authenticate"
# Non-interactive if CCLOUD_API_KEY is exported; otherwise opens a browser.
ccloud auth login --no-redirect || true
ccloud version

say "2. Provision the cluster"
# Basic is enough for this workload; --upgrade-type AUTOMATIC keeps the vector
# index feature available as versions roll forward.
if ccloud cluster list --output json | grep -q "\"name\": *\"${CLUSTER_NAME}\""; then
  echo "cluster ${CLUSTER_NAME} already exists, skipping create"
else
  ccloud cluster create basic "${CLUSTER_NAME}" \
    --cloud "${CLOUD}" \
    --region "${REGION}" \
    --upgrade-type AUTOMATIC
fi

say "3. Inspect what was provisioned"
ccloud cluster describe "${CLUSTER_NAME}" --output json

say "4. Create the SQL user and capture the connection string"
# The application user is deliberately NOT root. Rescind needs only DML on its
# own tables; see docs/LIMITS.md on access control.
ccloud cluster user create "${CLUSTER_NAME}" rescind_app || true
ccloud cluster sql "${CLUSTER_NAME}" --connection-string --database "${DB_NAME}" \
  || echo "connection string requires an existing database; create it below first"

say "5. Verify backup configuration"
# Point-in-time restore is the production answer to the garbage-collection
# window that bounds AS OF SYSTEM TIME replay. This is the check that confirms
# the retention actually in force, rather than the retention assumed.
ccloud cluster backup-config describe "${CLUSTER_NAME}" --output json \
  || echo "backup-config unavailable on this cluster tier -- record that fact"

say "6. Inspect audit / activity logs"
# Rescind's own audit trail lives in the retractions table. This is the
# complementary control-plane record: who touched the cluster itself.
ccloud audit-log list --limit 20 --output json \
  || echo "audit-log export may require an Advanced/Enterprise tier -- record that fact"

say "7. Apply the schema and verify on the real cluster"
cat <<'EOF'
Now point Rescind at the cluster and run the same verification CI runs:

  export RESCIND_DATABASE_URL='<connection string from step 4, database=rescind>'
  python scripts/apply_schema.py
  python scripts/probe_cockroach.py     # writes ci/probe.json for THIS cluster
  python scripts/seed.py
  pytest -v
  python scripts/record_demo.py

Then commit ci/probe.json and ci/ccloud-evidence.txt so the Cloud run is backed
by a receipt, and update the README's verification section to match what you saw.
EOF

say "Done"
