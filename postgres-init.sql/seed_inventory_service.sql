-- Seed data for inventory_service_db (PostgreSQL)
-- Run on inventory_service_db

TRUNCATE TABLE app_stocktransaction, app_inventory RESTART IDENTITY;

INSERT INTO app_inventory (id, variant_id, quantity, reserved_quantity, updated_at)
SELECT
    g,
    g,
    100 + (g % 50),
    (g % 8),
    NOW() - (g || ' hours')::interval
FROM generate_series(1, 200) AS g
ON CONFLICT (id) DO UPDATE SET
    quantity = EXCLUDED.quantity,
    reserved_quantity = EXCLUDED.reserved_quantity,
    updated_at = NOW();

INSERT INTO app_stocktransaction (id, variant_id, change_quantity, type, created_at)
SELECT
    g,
    ((g - 1) % 200) + 1,
    CASE WHEN g % 4 = 0 THEN -1 * ((g % 6) + 1) ELSE (g % 7) + 1 END,
    CASE g % 4
        WHEN 0 THEN 'SALE'
        WHEN 1 THEN 'IMPORT'
        WHEN 2 THEN 'ADJUST'
        ELSE 'RESERVE'
    END,
    NOW() - (g || ' hours')::interval
FROM generate_series(1, 500) AS g
ON CONFLICT (id) DO UPDATE SET
    change_quantity = EXCLUDED.change_quantity,
    type = EXCLUDED.type;

SELECT setval(pg_get_serial_sequence('app_inventory', 'id'), (SELECT GREATEST(MAX(id), 1) FROM app_inventory));
SELECT setval(pg_get_serial_sequence('app_stocktransaction', 'id'), (SELECT GREATEST(MAX(id), 1) FROM app_stocktransaction));
