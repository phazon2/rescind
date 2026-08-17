---
name: retracting-agent-memory
description: Designs retractable agent memory on CockroachDB so a withdrawn fact can be pulled back together with every conclusion derived from it. Covers making retracted state unreachable by vector retrieval via a STORED computed prefix column, walking lineage with WITH RECURSIVE inside one serializable transaction, flagging dependent decisions instead of reversing them, and replaying a past decision exactly with AS OF SYSTEM TIME at a stored cluster_logical_timestamp(). Use when an agent's memory must support recall, withdrawal, correction, expiry or right-to-erasure; when a stored fact can later be proven wrong; when regulated workflows require proving what an agent knew at a past moment; or when auditing whether retrieval can still surface data that has been withdrawn.
compatibility: Requires CockroachDB >= 25.2 for vector indexes (CREATE VECTOR INDEX) and SET CLUSTER SETTING feature.vector_index.enabled = true. Only L2 distance (<->) is index-accelerated. AS OF SYSTEM TIME replay is bounded by gc.ttlseconds (~4h default). Production-safe; all operations are ordinary SQL.
metadata:
  author: rescind
  version: "1.0"
  reference: https://github.com/phazon2/rescind
---

# Retracting Agent Memory

Most agent memory is append-only by accident. A fact gets embedded, retrieved,
summarised into other memories, and propagated into derived conclusions with no
lineage — so when the fact turns out to be wrong, nothing can be taken back.

This skill encodes the four database-level decisions that make retraction
possible, and the one design rule that keeps it trustworthy.

## When to Use This Skill

- An agent stores facts that can later be withdrawn, corrected, or expired
- A regulated workflow needs proof of what an agent knew at a past moment
- You need to know which past conclusions depended on a fact you just withdrew
- You are auditing whether retrieval can still surface withdrawn data
- You are choosing between a vector store and CockroachDB for agent memory

## Steps

### 1. Make retracted state a prefix column of the vector index

Do not filter retracted rows in application code. Application filters are
forgettable, and the one query that forgets is the one that leaks.

```sql
CREATE TABLE facts (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_id   STRING NOT NULL,
    claim        STRING NOT NULL,
    source       STRING NOT NULL,
    embedding    VECTOR(1024) NOT NULL,
    retracted_at TIMESTAMPTZ,
    retracted    BOOL NOT NULL AS (retracted_at IS NOT NULL) STORED,
    CONSTRAINT source_not_empty CHECK (length(btrim(source)) > 0)
);

CREATE VECTOR INDEX facts_live ON facts (subject_id, retracted, embedding);
```

CockroachDB will not use a vector index unless every prefix column is
equality-constrained. Retrieval is therefore *forced* to declare the filter:

```sql
SELECT id, claim, embedding <-> $1 AS distance
FROM facts
WHERE subject_id = $2 AND retracted = false
ORDER BY embedding <-> $1
LIMIT $3;
```

You cannot write the fast query and forget the filter, because the filter is
what makes the query fast. Verify with `EXPLAIN` that the plan names the index.

**Verified behaviour:** a STORED computed column *is* accepted as a vector-index
prefix column on CockroachDB v25.3.0.

### 2. Require provenance at write time, in the database

An unattributed memory cannot be retracted safely, because you cannot tell what
it came from or who else relied on it. Enforce it with a `CHECK` constraint, not
only in the application, so a second writer cannot bypass it.

### 3. Record lineage as real foreign keys

```sql
CREATE TABLE fact_edges (
    parent_id UUID NOT NULL REFERENCES facts (id) ON DELETE CASCADE,
    child_id  UUID NOT NULL REFERENCES facts (id) ON DELETE CASCADE,
    PRIMARY KEY (parent_id, child_id),
    INDEX fact_edges_by_child (child_id)
);
```

Refuse to write a derived fact with an empty parent list. A parentless
conclusion is invisible to every future retraction.

### 4. Retract the transitive closure in one serializable transaction

```sql
WITH RECURSIVE descendants (id) AS (
    SELECT unnest($1::UUID[])
  UNION
    SELECT e.child_id FROM fact_edges e JOIN descendants d ON e.parent_id = d.id
)
SELECT id FROM descendants;
```

`UNION` rather than `UNION ALL` deduplicates, which also makes the walk safe
against cycles. In the same transaction: mark the closure retracted, flag every
dependent decision, and write an audit row recording the blast radius.

A partial retraction is worse than none — it leaves conclusions standing on
facts the system has already disowned.

### 5. Retry on serialization failures

CockroachDB is SERIALIZABLE with optimistic concurrency, so this transaction can
be aborted with SQLSTATE 40001 and **must** be retried by the client with
exponential backoff. Make the transaction idempotent under replay: only move
facts from live to retracted, and only flag decisions not already flagged.

A retraction that gives up under contention is a retraction that did not happen.

### 6. Store an HLC so replay is exact

Store `cluster_logical_timestamp()` — not a wall clock — on every decision:

```sql
INSERT INTO decisions (question, verdict, decided_hlc)
VALUES ($1, $2, cluster_logical_timestamp());
```

Replay by pinning a read-only transaction to that exact snapshot:

```sql
BEGIN;
SET TRANSACTION AS OF SYSTEM TIME <hlc>;
-- the SAME retrieval query, byte for byte
COMMIT;
```

Run the identical query against the historical snapshot and the present. The
difference between the two answers is precisely what the agent has un-learned.
Wall-clock replay is an approximation that can straddle concurrent writes; this
is not.

## The design rule

**Flag dependent decisions. Never silently reverse them.**

A retraction invalidates the *basis* for a past decision; it does not
automatically determine the new decision. Reversing a shipment release, a
payment, or a clinical recommendation is a human's call. A system that reversed
it automatically would be its own kind of untrustworthy.

## Anti-patterns

| Anti-pattern | Why it fails |
|---|---|
| `WHERE retracted = false` only in application code | One forgetful query leaks withdrawn memory |
| Soft-delete flag with no index relationship | Retrieval can still reach it |
| Derived facts without lineage | Nothing to cascade over; retraction becomes guesswork |
| Deleting retracted rows outright | Destroys the audit trail that makes replay possible |
| Wall-clock timestamps for replay | Can straddle concurrent writes; not the snapshot actually read |
| No 40001 retry | A recall silently fails under contention |
| Cosine distance with a vector index | Only L2 (`<->`) is index-accelerated in CockroachDB |

## Validation

- `EXPLAIN` the retrieval query; confirm the plan names the vector index.
- Retract a root fact and assert every transitive descendant is unreachable.
- Roll back mid-retraction and assert no fact, no flag and no audit row survives.
- Replay a decision and assert the historical answer differs from the present one.
