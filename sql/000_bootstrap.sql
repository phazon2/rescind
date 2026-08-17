-- Vector indexes are gated behind a cluster setting.
--
-- On a self-hosted or single-node cluster this succeeds. On some CockroachDB
-- Cloud Basic clusters the setting is not user-settable; scripts/apply_schema.py
-- treats a failure here as non-fatal and records it, because retrieval remains
-- CORRECT without the index (CockroachDB falls back to an exact scan with the
-- same <-> ordering) -- just unindexed. See docs/LIMITS.md.
SET CLUSTER SETTING feature.vector_index.enabled = true;
