-- One realistic recall scenario.
--
-- Northvale Dairy Co-op ships infant formula to a Meridian Foods distribution
-- centre. On 17 August 2026 the supplier issues a recall on lot
-- LOT-2026-0619-NV. Four minutes later, before Rescind existed, the agent would
-- still have been telling the DC the lot was fine to ship.
--
-- The physical world lives here. The agent's MEMORY of it is seeded by
-- scripts/seed.py, because facts carry embeddings.

DELETE FROM decision_support;
DELETE FROM retractions;
DELETE FROM decisions;
DELETE FROM fact_edges;
DELETE FROM facts;
DELETE FROM shipments;
DELETE FROM lots;

INSERT INTO lots (lot_id, product_name, supplier, manufactured_on, status) VALUES
    ('LOT-2026-0619-NV', 'Infant Formula, Stage 1, 400g tin',
     'Northvale Dairy Co-op', '2026-06-19', 'active'),
    ('LOT-2026-0620-NV', 'Infant Formula, Stage 1, 400g tin',
     'Northvale Dairy Co-op', '2026-06-20', 'active');

INSERT INTO shipments (shipment_id, lot_id, destination, units, status) VALUES
    ('SHP-88412', 'LOT-2026-0619-NV', 'Meridian Foods DC-7, Sacramento CA', 4800, 'staged'),
    ('SHP-88413', 'LOT-2026-0620-NV', 'Meridian Foods DC-7, Sacramento CA', 3600, 'staged');
