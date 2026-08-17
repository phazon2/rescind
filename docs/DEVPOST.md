# Devpost submission copy

Paste-ready. Submit a draft early, then refine — a submitted draft beats a
perfect unsubmitted entry.

---

## Project name

**Rescind**

## Tagline (short)

Retractable agent memory. When a lot is recalled, every conclusion built on it
comes down with it.

## Elevator pitch / description

**When a lot is recalled, Rescind pulls back every conclusion the agent built on
it — in one transaction, with proof of what the agent knew before and after.**

At 15:00, Northvale Dairy Co-op recalls lot LOT-2026-0619-NV — Cronobacter
detected in a retained sample. At 15:04, the AI agent tells Meridian Foods DC-7
that 4,800 tins of infant formula are cleared for release. The agent is not
malfunctioning. It is remembering a Certificate of Analysis that no longer
exists, and three conclusions it derived from that certificate, none of which
know where they came from.

**You cannot deploy an agent into a recall workflow today, because you cannot
prove what it knew and you cannot take back what it learned.**

Everyone reads "agentic memory" as memory that accumulates: remember more,
remember longer, recall better. Mem0, Zep, Letta and Pinecone are all good at
that, and not one of them can take a fact back. Retracting a memory safely needs
three things at once — transactions, foreign keys, and time travel — and no vector
store has any of the three.

CockroachDB has all three. So Rescind inverts the premise: **memory that can be
un-learned.**

Three properties do the work:

1. **Retracted memory is physically unreachable by retrieval, not filtered in
   application code.** `facts.retracted` is a STORED computed column used as a
   *prefix column* of the vector index. CockroachDB will not use a vector index
   unless every prefix column is equality-constrained, so every semantic search
   is forced to declare `retracted = false`. You cannot write the fast query and
   forget the filter, because the filter is what makes the query fast. The
   committed `EXPLAIN` output confirms the plan uses that index.

2. **Retraction is one serializable transaction.** A `WITH RECURSIVE` walk over a
   real foreign-key lineage graph retracts the full transitive descendant set,
   flags every standing decision that rested on any of it, and writes an audit row
   recording the blast radius. All of it commits together or not at all — a
   partial retraction is worse than none, because it leaves conclusions standing
   on facts the system has already disowned. Decisions are *flagged, never
   silently reversed*: reversing a shipment release is a human's call.

3. **Replay is exact, not reconstructed.** Decisions store
   `cluster_logical_timestamp()` — a hybrid logical clock, not a wall clock — so
   `AS OF SYSTEM TIME` replay reads the identical MVCC snapshot the agent read.
   In the recorded run the same query returns 4 memories at the decision's HLC and
   1 now.

The vertical is product recall in food and pharmaceutical distribution. The buyer
is a Director of Quality Assurance or recall coordinator at a distributor. The
budget line is FSMA 204, the FDA Food Traceability Rule, compliance date
**20 July 2028** — a date the FDA extended in a Federal Register notice of
7 August 2025.

Competitors become customers: Rescind exposes an MCP server, so Mem0, Zep, Letta
or any MCP client can ask *is this memory still live?*, *what did the agent know
when it decided that?*, and *pull this back, and everything built on it.* The
incumbent keeps the recall-and-ranking business it is good at; Rescind becomes
the system of record for what may still be believed.

**Verified, not asserted:** 19 of 19 tests pass against a real CockroachDB
v25.3.0 cluster on every push, with no database mocks anywhere — the behaviour
under test only exists in CockroachDB, so mocking it would certify nothing. The
machine-readable receipt is committed at `ci/latest.json`, and 5 of 6 assumption
probes are recorded in `ci/probe.json`. What was *not* verified is stated just as
plainly in the README and in `docs/LIMITS.md`.

---

## Which CockroachDB tools did you use, and what did the agent actually do with them?

**Two of the four listed tools, both meaningfully integrated — with the evidence.**

**1. Distributed Vector Indexing.** Two vector indexes on the `facts` table. The
critical one is `facts_live_by_lot (lot_id, retracted, embedding)`, where the
retraction flag is a **prefix column**. CockroachDB will not use a vector index
unless every prefix column is equality-constrained, so every semantic retrieval
is forced to declare `retracted = false`. That is what makes retracted memory
*unreachable* rather than merely filtered — you cannot write the fast query and
forget the filter, because the filter is what makes the query fast. L2 (`<->`)
throughout, since only L2 is index-accelerated. `ci/probe.json` records the
`EXPLAIN` plan naming that index in use on a live cluster.

**2. Agent Skills Repo.** Installed with
`npx skills add cockroachlabs/cockroachdb-skills` — 34 skills, each pinned by
content hash in `skills-lock.json` — and used to audit this codebase. This was
not decoration; it found real defects:

- The `designing-application-transactions` skill's retry guidance surfaced that
  the retraction transaction had **no client-side retry**. CockroachDB runs
  SERIALIZABLE with optimistic concurrency and can abort any transaction with
  SQLSTATE 40001. Without retry, a concurrent writer touching the same lot could
  make a recall silently fail — leaving conclusions standing on facts the system
  had already disowned, which is the exact condition this project exists to
  prevent. `rescind/retry.py` (exponential backoff, idempotent under replay,
  deferring to an enclosing transaction rather than retrying a savepoint against
  a stale snapshot) and its six tests exist because of that audit.
- The same skill flagged `SELECT *`, now replaced with explicit column
  projections.

Rescind contributes back rather than only consuming: it ships a spec-conformant
skill of its own at `skills/retracting-agent-memory/SKILL.md`, encoding the
retractable-memory design so any agent framework can apply it.

**Also used, though not among the four:** serializable transactions and foreign
keys (the `WITH RECURSIVE` cascade over the lineage graph, with a test that rolls
back mid-retraction and asserts no fact, no flag and no audit row survives);
`AS OF SYSTEM TIME` MVCC time travel pinned to `cluster_logical_timestamp()`; and
computed columns, partial indexes, UUID arrays and `CHECK` constraints for the
audit and provenance layer.

**On MCP, stated precisely:** `rescind/mcp_server.py` implements an MCP server
exposing four tools (`rescind_retrieve`, `rescind_replay`, `rescind_recall_lot`,
`rescind_open_reviews`). This is *Rescind's own* MCP server — it is **not**
CockroachDB's Cloud Managed MCP Server, which requires a Cloud cluster. We do not
claim that one.

**Not exercised:** CockroachDB Cloud, the Managed MCP Server, and the `ccloud`
CLI. The build environment allowed outbound port 443 only, so the CockroachDB SQL
port (26257) was unreachable and the binary download host was blocked by egress
policy. Verification therefore runs against a single-node CockroachDB v25.3.0
cluster started inside GitHub Actions. The control-plane work is scripted in
`scripts/ccloud_setup.sh` — provision, describe, non-root SQL user, backup
configuration, audit log — and labelled as not yet executed rather than listed as
done.

## Which AWS services did you use, and what did the agent actually do with them?

**Integrated in code:** AWS Bedrock, for both halves of the reasoning path —
`amazon.titan-embed-text-v2:0` for 1024-dimension normalised embeddings, and
Claude for the release/hold recommendation. Two safety properties live in that
integration: the system prompt states that an empty or silent record set does not
clear a lot (an agent that reads "no recall notice found" as an all-clear is
exactly the failure this project prevents), and a malformed model response
**fails closed** — it holds the lot and says so, rather than inventing a verdict.

**Not exercised against live AWS, stated plainly:** the credentials available in
the build environment were rejected by AWS STS (`InvalidClientTokenId`), so no
Bedrock call was ever made. CI and the recorded demo use deterministic
topic-anchored stand-in vectors from `rescind/topics.py` instead. That substitution
is disclosed in the README, in `docs/LIMITS.md`, and on the face of the demo page
itself. Only the vectors are substituted; with valid credentials the identical code
path calls Bedrock, warns loudly, and stamps `decisions.offline_mode = false`.

Lambda and S3 are *not* claimed: neither was deployed, and listing them would be
the kind of unearned checkbox this submission is trying not to rely on.

---

## Built with

CockroachDB v25.3.0 · distributed vector indexing · AS OF SYSTEM TIME · AWS
Bedrock (Titan, Claude) · Python 3.11 · psycopg 3 · MCP · GitHub Actions

## Links

> **DO THIS FIRST: merge the work onto `main`.** A judge who opens
> github.com/phazon2/rescind lands on the default branch. Until the branch
> `claude/rescind-hackathon-handoff-1qj0lb` is merged, that page shows an almost
> empty repository and every `blob/main/...` link 404s. This is the single highest-value
> action on the list.
>
> **Open the demo link once before pasting it.** The demo is published from the
> `gh-pages` branch by the `publish-demo` workflow, and GitHub's "pages build and
> deployment" job has run against it. Confirm
> `https://phazon2.github.io/rescind/` renders — a 404 on the demo link is worse
> than no demo link.
>
> If it does 404, Pages needs enabling once: **Settings → Pages → Build and
> deployment → Deploy from a branch → Branch: `gh-pages` / `(root)`**. Nothing
> else needs changing; the branch already holds the built page. `web/index.html`
> also renders correctly opened straight from disk, which is a usable fallback for
> recording the video.

- **Repository:** https://github.com/phazon2/rescind
- **Demo:** https://phazon2.github.io/rescind/
- **CI receipt:** https://github.com/phazon2/rescind/blob/main/ci/latest.json
- **Limits, in full:** https://github.com/phazon2/rescind/blob/main/docs/LIMITS.md
- **Architecture diagram:** https://github.com/phazon2/rescind/blob/main/docs/architecture.svg

## Build disclosure (required by the rules)

Every line in this repository was written during the submission period; no
pre-existing code was incorporated. Built with AI coding assistance (Claude
Code), which the rules expressly permit. Third-party dependencies: psycopg,
boto3, pytest, and the CockroachDB Agent Skills repo (Apache-2.0), consumed via
`npx skills add` and not vendored. Licensed MIT, with the LICENSE file at the
repository root so it is detected in the About section.

## Hackathon

CockroachDB × AWS Hackathon — Build with Agentic Memory. Diego Radrigan
([@phazon2](https://github.com/phazon2)), solo entry. MIT licensed.
