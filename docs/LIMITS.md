# Limits

Everything Rescind does not do, stated plainly. The README makes one claim
without hedging; this file is where the hedges live, and it is meant to be
complete rather than flattering.

If you are evaluating this project, read this file. Anything here that is not
here would be a defect in the honesty of the submission.

---

## What was built in a sandbox and what was verified on a real cluster

This matters more than anything else in this file, so it is first.

Every test in `tests/` runs against a **real CockroachDB cluster** — a
single-node in-memory cluster started on the CI runner. There are no database
mocks anywhere in the suite. `ci/latest.json` is written by that run and records
which cluster version it ran against and which assertions passed. That file
records **what a run observed**. The docstring on each test states **what the
test certifies**. Those are different claims and this repository keeps them
separate deliberately.

What was **not** verified:

- **No CockroachDB Cloud cluster.** The build environment permitted outbound
  traffic on port 443 only, so the CockroachDB SQL port (26257) was unreachable
  and `binaries.cockroachdb.com` was blocked by egress policy. Everything was
  therefore verified against a self-hosted single-node cluster in CI instead.
- **No multi-node or multi-region behaviour.** Nothing here has been observed
  under a network partition, a range split, or a follower read. The claims about
  serializability and MVCC snapshots rest on CockroachDB's guarantees, not on
  our own testing of them at scale.
- **No live AWS Bedrock call.** See the next section.

## Embeddings are not real in the recorded demo

The AWS credentials available in the build environment were rejected by AWS STS
(`InvalidClientTokenId`), so **no Titan embedding call and no Claude call was
ever made from this build**. Two consequences:

1. **CI and the recorded demo use deterministic stand-in vectors.**
   `rescind/topics.py` assigns each named topic its own axis and builds unit
   vectors from topic weights. A fact and a question sharing topics land close
   together *by construction*. This exercises the retrieval, threshold, refusal
   and cascade paths exactly as real embeddings would, and it is reproducible on
   any machine — but it encodes the topic labels `scripts/seed.py` assigns, not
   the meaning of the text. It is not semantics.
2. **`amazon.titan-embed-text-v2:0` returning exactly 1024 dimensions with
   `normalize: true` is unverified.** The schema hardcodes `VECTOR(1024)`. If
   Titan returns a different width, `rescind/bedrock.py` raises rather than
   silently truncating, but the schema would need changing. The probe that would
   confirm this (`titan_embedding_dimensions` in `scripts/probe_cockroach.py`)
   reports "skipped" whenever `RESCIND_OFFLINE` is set, which is the case in CI.

The substituted component is *only* the vectors. With valid credentials the
identical code path calls Bedrock, and `bedrock.py` warns loudly and stamps
`decisions.offline_mode = true` on every decision it touches, so an offline
decision can never be mistaken for a real one after the fact.

The tests do not depend on either embedder: they supply their own controlled
vectors at exact cosine similarities, so the threshold assertions are stable
without a model in the loop.

## Time travel is bounded by garbage collection

`replay()` reads `AS OF SYSTEM TIME <decided_hlc>`. That only works while the
MVCC history still exists. It is bounded by `gc.ttlseconds`, which defaults to
roughly 4 hours on recent CockroachDB versions.

So: replaying a decision from this morning works. Replaying a decision from last
quarter — which is exactly what an FDA investigator would ask for — **does
not**, and `replay()` will raise rather than return a plausible-looking
approximation.

A production deployment would need one of: a raised `gc.ttlseconds` on the
`facts` table (costly in storage), scheduled `BACKUP` with
point-in-time-restore, or a periodic materialisation of decision snapshots into
an append-only audit table. None of those are built. This is the single largest
gap between the demo and a shippable compliance product, and it is a real
engineering problem, not a configuration flag.

## Retraction is not deletion

A retracted fact is still in the `facts` table with `retracted_at` set. It is
unreachable by semantic retrieval, which is the guarantee the project makes, but
it is deliberately still readable by a direct primary-key query — replay depends
on that, and so does any audit of what the agent used to believe.

This means Rescind is **not** a data-erasure mechanism. It does not implement a
GDPR right-to-erasure path, and "retract" should not be read as "delete". A real
purge path would have to reckon with the fact that erasing history destroys the
audit trail that makes the rest of the system trustworthy — those two
requirements genuinely conflict, and Rescind currently chooses auditability.

## The cascade only knows the lineage it was told about

`retract()` walks `fact_edges`. If an agent derives a conclusion without calling
`derive_fact()` — writing it through raw SQL, or holding it in a prompt, in a
cache, in a downstream system, or in an email it already sent — that conclusion
is invisible to the cascade and will not be pulled back.

`derive_fact()` refuses to create a parentless derived fact, and the `facts`
table enforces non-empty provenance with a `CHECK` constraint that a second
writer cannot bypass. Those narrow the hole. They do not close it. **Rescind can
only retract what was written down through it**, and a deployment's real
coverage is a function of how disciplined its write path is.

## The refusal threshold is hand-set, not calibrated

`MIN_SUPPORTING_FACTS = 2` and `MAX_SUPPORTING_DISTANCE = 0.55` are chosen
numbers. 0.55 in L2 corresponds to roughly 0.85 cosine for unit-normalised
vectors, which is a defensible starting point and nothing more. They have not
been tuned against a labelled corpus of real recall decisions, because no such
corpus was available.

The threshold is deterministic, which is the property that matters for
auditability and for CI — it behaves identically on every run. Deterministic is
not the same as correct. A deployment would need to calibrate these against real
outcomes and would need a false-negative review process, since the failure mode
of a too-strict threshold is an agent that refuses to answer anything useful.

## Vector index caveats

- Only L2 distance (`<->`) is index-accelerated in CockroachDB. Cosine and inner
  product are not, so the code uses `<->` throughout.
- Vector indexes require `SET CLUSTER SETTING feature.vector_index.enabled =
  true`. `scripts/apply_schema.py` applies this tolerantly, because it may not be
  user-settable on some managed clusters. If it fails, retrieval remains
  **correct** — CockroachDB falls back to an exact scan with the same `<->`
  ordering — but unindexed, which is acceptable at demo scale and would not be at
  production scale.
- The `retracted = false` guarantee is a property of *index-eligible query
  shape*, not a permission boundary. A sufficiently determined caller can write
  `WHERE retracted = true` and read retracted memory. The design forces the
  retrieval path to be explicit about it; it does not prevent a deliberate
  bypass. Preventing that is a job for column-level access control, which is not
  implemented.

## Security and access control are demo-grade

- `retractions.actor` is a **free-text string**, not an authenticated principal.
  Anyone who can call `retract()` can claim to be anyone. There is no
  authentication, no authorisation, and no signing anywhere in this codebase.
- The CI cluster runs `--insecure`. A real deployment needs TLS, per-role SQL
  users, and a non-`root` application user with only the privileges it needs.
- There is no rate limiting, no input size limit on claims or sources, and no
  tenant isolation. A single shared database is assumed.
- The audit trail is append-only **by convention**, not by constraint. Nothing
  stops a privileged user from `UPDATE`-ing or `DELETE`-ing rows in
  `retractions`. Making that impossible needs either row-level security or an
  external append-only log.

## Product scope

- **Decisions are flagged, never reversed.** This is deliberate — reversing a
  shipment release is a human's call — but it means Rescind's output is a review
  queue, and a review queue nobody works is worth nothing. There is no
  escalation, no notification, no SLA, and no way to record that a human cleared
  a flagged decision. `open_reviews()` shows the queue; nothing closes it.
- **One recall scenario is seeded.** `sql/002_seed.sql` and `scripts/seed.py`
  build a single lot with three observations and three derived conclusions. That
  is a demonstration, not a load test — `scripts/benchmark_scale.py` is the load
  test, and it is where the next bullet's numbers come from.
- **The retraction cascade has a measured ceiling, and it is not large.**
  `scripts/benchmark_scale.py` grows a synthetic lineage graph and sweeps the
  cascade until a single transaction can no longer commit it. `ci/scale.json`
  records where that happened on the CI runner: a closure of **127 facts
  committed in one transaction; 511 exhausted the retry budget and was not
  applied.** `WITH RECURSIVE` over a wide graph is exactly where this design
  hurts first, which was the prediction, now measured instead of guessed.

  The failure mode is at least the safe one: `RetryExhausted` is raised, nothing
  is applied, and no partial retraction lands — the all-or-nothing property holds
  even at the ceiling. But a recall whose blast radius exceeds it would have to
  be split into several transactions, and **Rescind does not split it for you**.
  That is the single largest piece of engineering standing between this and a
  production deployment.
- **FSMA 204 is cited as the budget line, not as a compliance claim.** Rescind
  is not a validated compliance system, has not been assessed against 21 CFR
  Part 11, and would not satisfy an FDA audit as built. The compliance date is
  a real deadline (20 July 2028, extended by the FDA in a Federal Register
  notice of 7 August 2025); what Rescind does is address one narrow problem that
  sits inside that deadline's scope.

## Integration honesty

The hackathon asks which CockroachDB tools and AWS services were used. The
README answers that, and this file records the gap between "used" and
"meaningfully driven":

- Anything the README describes as verified is backed by `ci/latest.json` or by
  a probe result in `ci/probe.json`.
- Any integration that could not be exercised from the build environment is
  named as such in the README rather than being quietly listed. Read the
  integration table there with this section beside it.

## The demo page is a recording, not a live service

`web/index.html` renders `web/data.js`, which `scripts/record_demo.py` generated
by running the real scenario against a real CockroachDB cluster in CI. Every id,
hybrid logical clock, distance and count on that page came from that run.

It is nonetheless a **recording**. Clicking the recall button does not execute a
transaction against a live cluster; it advances the page between two states that
were both captured from one. The reason is that no publicly reachable cluster
existed to point a live demo at, and a live demo backed by nothing would have
been worse than an honest recording. The page says so in its own footer.

To run the same scenario live against your own cluster:
`python scripts/record_demo.py` with `RESCIND_DATABASE_URL` set — it performs
exactly the operations the page depicts.
