-- Rescind: schema for retractable agent memory.
--
-- Three CockroachDB properties do the load-bearing work here. They are the
-- submission, not decoration:
--
--   1. facts.retracted is a STORED computed column used as a PREFIX COLUMN of
--      the vector index. CockroachDB will not use a vector index unless every
--      prefix column is equality-constrained, so every semantic retrieval is
--      FORCED to declare `retracted = false`. Retracted memory is physically
--      unreachable by retrieval -- not filtered out in application code.
--
--   2. fact_edges gives derived conclusions real lineage, with real foreign
--      keys, so a retraction can walk the transitive closure and pull down
--      everything built on a withdrawn fact inside ONE serializable
--      transaction.
--
--   3. decisions.decided_hlc stores cluster_logical_timestamp() -- an HLC, not
--      a wall clock -- so AS OF SYSTEM TIME replay reads the identical MVCC
--      snapshot the agent read. Exact, not reconstructed.
--
-- Vector indexes require this cluster setting; see sql/000_bootstrap.sql.

-- ---------------------------------------------------------------------------
-- Physical world: lots and the shipments that carry them.
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS lots (
    lot_id          STRING PRIMARY KEY,
    product_name    STRING NOT NULL,
    supplier        STRING NOT NULL,
    manufactured_on DATE NOT NULL,
    status          STRING NOT NULL DEFAULT 'active',
    recalled_at     TIMESTAMPTZ,
    CONSTRAINT lots_status_valid CHECK (status IN ('active', 'recalled'))
);

CREATE TABLE IF NOT EXISTS shipments (
    shipment_id STRING PRIMARY KEY,
    lot_id      STRING NOT NULL REFERENCES lots (lot_id),
    destination STRING NOT NULL,
    units       INT NOT NULL,
    status      STRING NOT NULL DEFAULT 'staged',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT shipments_status_valid
        CHECK (status IN ('staged', 'released', 'held')),
    INDEX shipments_by_lot (lot_id)
);

-- ---------------------------------------------------------------------------
-- Memory: facts the agent knows, and the lineage between them.
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS facts (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lot_id           STRING NOT NULL REFERENCES lots (lot_id),
    kind             STRING NOT NULL,
    claim            STRING NOT NULL,

    -- Provenance is mandatory at write time. An unattributed memory cannot be
    -- retracted safely, so it is never stored. Enforced in the database, not
    -- only in Python -- a second writer cannot bypass it.
    source           STRING NOT NULL,

    embedding        VECTOR(1024) NOT NULL,

    asserted_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    asserted_hlc     DECIMAL NOT NULL,

    retracted_at     TIMESTAMPTZ,
    retracted_reason STRING,

    -- The whole design turns on this column. Because it is a prefix of the
    -- vector index below, retrieval cannot omit it.
    retracted        BOOL NOT NULL AS (retracted_at IS NOT NULL) STORED,

    CONSTRAINT facts_kind_valid CHECK (kind IN ('observation', 'derived')),
    CONSTRAINT facts_source_not_empty CHECK (length(btrim(source)) > 0),
    CONSTRAINT facts_claim_not_empty CHECK (length(btrim(claim)) > 0)
);

-- Vector index #1: per-lot semantic recall. (lot_id, retracted) must both be
-- equality-constrained for CockroachDB to use this index, which is exactly the
-- guarantee we want to be unable to forget.
CREATE VECTOR INDEX IF NOT EXISTS facts_live_by_lot
    ON facts (lot_id, retracted, embedding);

-- Vector index #2: cross-lot semantic recall, for "have we seen this failure
-- mode anywhere before?" Still gated on retracted.
CREATE VECTOR INDEX IF NOT EXISTS facts_live_global
    ON facts (retracted, embedding);

-- Lineage. A derived fact records every parent it was built on, so retraction
-- has a graph to walk instead of a guess to make.
CREATE TABLE IF NOT EXISTS fact_edges (
    parent_id UUID NOT NULL REFERENCES facts (id) ON DELETE CASCADE,
    child_id  UUID NOT NULL REFERENCES facts (id) ON DELETE CASCADE,
    PRIMARY KEY (parent_id, child_id),
    INDEX fact_edges_by_child (child_id)
);

-- ---------------------------------------------------------------------------
-- Decisions the agent has already handed to a human, and what they rested on.
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS decisions (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lot_id        STRING NOT NULL REFERENCES lots (lot_id),
    question      STRING NOT NULL,
    verdict       STRING NOT NULL,
    rationale     STRING NOT NULL,
    decided_at    TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- An HLC, not a wall clock. This is what makes replay exact.
    decided_hlc   DECIMAL NOT NULL,

    -- Decisions are FLAGGED, never silently reversed. Reversing a shipment
    -- release is a human's call.
    needs_review  BOOL NOT NULL DEFAULT false,
    review_reason STRING,

    model_id      STRING,
    offline_mode  BOOL NOT NULL DEFAULT false,

    CONSTRAINT decisions_verdict_valid
        CHECK (verdict IN ('release', 'hold', 'refused')),
    INDEX decisions_by_lot (lot_id),
    INDEX decisions_needing_review (needs_review) WHERE needs_review
);

-- The exact supporting set for a decision, with the distance at which each
-- fact was recalled. This is the "proof of what the agent knew".
CREATE TABLE IF NOT EXISTS decision_support (
    decision_id UUID NOT NULL REFERENCES decisions (id) ON DELETE CASCADE,
    fact_id     UUID NOT NULL REFERENCES facts (id),
    distance    FLOAT8 NOT NULL,
    PRIMARY KEY (decision_id, fact_id),
    INDEX decision_support_by_fact (fact_id)
);

-- ---------------------------------------------------------------------------
-- Audit: the blast radius of every retraction, written in the same
-- transaction as the retraction itself.
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS retractions (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lot_id               STRING NOT NULL,
    reason               STRING NOT NULL,
    actor                STRING NOT NULL,
    root_fact_ids        UUID[] NOT NULL,
    retracted_fact_ids   UUID[] NOT NULL,
    flagged_decision_ids UUID[] NOT NULL,
    facts_retracted      INT NOT NULL,
    decisions_flagged    INT NOT NULL,
    retracted_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    retracted_hlc        DECIMAL NOT NULL,
    CONSTRAINT retractions_reason_not_empty CHECK (length(btrim(reason)) > 0),
    INDEX retractions_by_lot (lot_id)
);
