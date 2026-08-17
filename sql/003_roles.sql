-- Least-privilege application role.
--
-- Written after auditing Rescind with the CockroachDB Agent Skills repo's
-- `hardening-user-privileges` skill. The application does not need, and must not
-- have, the ability to destroy the record of what it did.
--
-- Two grants are deliberately absent, and they are the point:
--
--   * NO DELETE anywhere. The application literally cannot delete a fact, a
--     lineage edge, a decision or an audit row. Retraction is an UPDATE that
--     sets retracted_at; it is not a delete, and the role could not delete even
--     if a bug tried to.
--   * NO UPDATE on `retractions`. Audit rows are insert-only at the privilege
--     level, not append-only by convention. A compromised application cannot
--     rewrite the history of what it retracted.
--
-- No DDL either: the role cannot DROP or ALTER anything, so a SQL-injection
-- foothold in the application cannot reshape the schema.
--
-- scripts/check_least_privilege.py proves each of these on a live cluster.

CREATE USER IF NOT EXISTS rescind_app;

GRANT CONNECT ON DATABASE rescind TO rescind_app;
GRANT USAGE ON SCHEMA public TO rescind_app;

-- CockroachDB grants CREATE on the public schema to the `public` role by
-- default, which let rescind_app create its own tables -- verified by
-- scripts/check_least_privilege.py, which caught this. Revoke it: an
-- application that cannot DROP the schema should not be able to grow it either.
REVOKE CREATE ON SCHEMA public FROM public;
REVOKE CREATE ON SCHEMA public FROM rescind_app;

-- Physical world: read, and update status when a lot is recalled.
GRANT SELECT, UPDATE ON TABLE lots TO rescind_app;
GRANT SELECT, UPDATE ON TABLE shipments TO rescind_app;

-- Memory: write new facts, and mark existing ones retracted. Never delete.
GRANT SELECT, INSERT, UPDATE ON TABLE facts TO rescind_app;

-- Lineage is immutable once written: a derived fact's parents never change.
GRANT SELECT, INSERT ON TABLE fact_edges TO rescind_app;

-- Decisions: write them, and flag them for review. Never delete.
GRANT SELECT, INSERT, UPDATE ON TABLE decisions TO rescind_app;

-- The supporting set of a decision is immutable once recorded.
GRANT SELECT, INSERT ON TABLE decision_support TO rescind_app;

-- The audit trail is INSERT-only. No UPDATE, no DELETE.
GRANT SELECT, INSERT ON TABLE retractions TO rescind_app;
