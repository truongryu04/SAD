-- Seed data for attribute_service_db (PostgreSQL)
-- Run on attribute_service_db

TRUNCATE TABLE app_productattributevalue, app_categoryattribute, app_attribute RESTART IDENTITY;

INSERT INTO app_attribute (id, name, data_type, unit, created_at)
VALUES
    (1,  'Kich thuoc man hinh', 'number', 'inch', NOW() - INTERVAL '30 days'),
    (2,  'RAM', 'number', 'GB', NOW() - INTERVAL '30 days'),
    (3,  'Bo nho trong', 'number', 'GB', NOW() - INTERVAL '30 days'),
    (4,  'Dung luong pin', 'number', 'mAh', NOW() - INTERVAL '30 days'),
    (5,  'Chipset', 'text', '', NOW() - INTERVAL '30 days'),
    (6,  'He dieu hanh', 'text', '', NOW() - INTERVAL '30 days'),
    (7,  'CPU', 'text', '', NOW() - INTERVAL '30 days'),
    (8,  'GPU', 'text', '', NOW() - INTERVAL '30 days'),
    (9,  'Trong luong', 'number', 'kg', NOW() - INTERVAL '30 days'),
    (10, 'Loai phu kien', 'select', '', NOW() - INTERVAL '30 days'),
    (11, 'Tuong thich', 'text', '', NOW() - INTERVAL '30 days'),
    (12, 'Mau sac', 'text', '', NOW() - INTERVAL '30 days'),
    (13, 'Bao hanh', 'number', 'thang', NOW() - INTERVAL '30 days'),
    (14, 'Kha nang chong nuoc', 'text', '', NOW() - INTERVAL '30 days'),
    (15, 'Chat lieu day deo', 'text', '', NOW() - INTERVAL '30 days'),
    (16, 'Ket noi', 'text', '', NOW() - INTERVAL '30 days'),
    (17, 'Camera sau', 'number', 'MP', NOW() - INTERVAL '30 days');

WITH schema_map AS (
    SELECT * FROM (VALUES
        -- Dien thoai + nhanh thuong hieu dien thoai
        (1, 1,  true, 1), (1, 2,  true, 2), (1, 3,  true, 3), (1, 4,  true, 4), (1, 5,  true, 5), (1, 6,  true, 6), (1, 17, false, 7),
        (6, 1,  true, 1), (6, 2,  true, 2), (6, 3,  true, 3), (6, 4,  true, 4), (6, 5,  true, 5), (6, 6,  true, 6), (6, 17, true,  7),
        (7, 1,  true, 1), (7, 2,  true, 2), (7, 3,  true, 3), (7, 4,  true, 4), (7, 5,  true, 5), (7, 6,  true, 6), (7, 17, true,  7),
        (8, 1,  true, 1), (8, 2,  true, 2), (8, 3,  true, 3), (8, 4,  true, 4), (8, 5,  true, 5), (8, 6,  true, 6), (8, 17, true,  7),

        -- Laptop + nhanh thuong hieu laptop
        (2, 1,  true, 1), (2, 2,  true, 2), (2, 3,  true, 3), (2, 7,  true, 4), (2, 8,  false, 5), (2, 9,  false, 6), (2, 13, true, 7),
        (9, 1,  true, 1), (9, 2,  true, 2), (9, 3,  true, 3), (9, 7,  true, 4), (9, 8,  false, 5), (9, 9,  false, 6), (9, 13, true, 7),
        (10,1,  true, 1), (10,2,  true, 2), (10,3,  true, 3), (10,7,  true, 4), (10,8,  false, 5), (10,9,  false, 6), (10,13,true, 7),

        -- Tablet
        (3, 1,  true, 1), (3, 2, true, 2), (3, 3, true, 3), (3, 4, true, 4), (3, 6, true, 5), (3, 16, false, 6),

        -- Smartwatch
        (4, 1,  true, 1), (4, 4, true, 2), (4, 11, true, 3), (4, 14, false, 4), (4, 15, false, 5), (4, 16, true, 6), (4, 13, true, 7),

        -- Phu kien
        (5, 10, true, 1), (5, 11, true, 2), (5, 12, false, 3), (5, 13, true, 4), (5, 16, false, 5)
    ) AS t(category_id, attribute_id, is_required, display_order)
)
INSERT INTO app_categoryattribute (id, category_id, attribute_id, is_required, display_order)
SELECT
    ROW_NUMBER() OVER (ORDER BY category_id, display_order) AS id,
    category_id,
    attribute_id,
    is_required,
    display_order
FROM schema_map;

WITH seeded_products AS (
    SELECT
        g AS product_id,
        ((g - 1) / 10) + 1 AS category_id,
        ((g - 1) % 10) + 1 AS idx
    FROM generate_series(1, 100) AS g
)
INSERT INTO app_productattributevalue (id, product_id, attribute_id, value)
SELECT
    ROW_NUMBER() OVER (ORDER BY p.product_id, ca.display_order) AS id,
    p.product_id,
    ca.attribute_id,
    CASE ca.attribute_id
        WHEN 1 THEN (6 + (p.idx % 8))::text
        WHEN 2 THEN (4 * (1 + (p.idx % 4)))::text
        WHEN 3 THEN (64 * (1 + (p.idx % 4)))::text
        WHEN 4 THEN (3000 + (p.idx % 8) * 600)::text
        WHEN 5 THEN CASE p.category_id
            WHEN 6 THEN 'Apple A' || (16 + (p.idx % 3))
            WHEN 7 THEN 'Snapdragon ' || (7 + (p.idx % 3)) || ' Gen ' || (1 + (p.idx % 3))
            WHEN 8 THEN 'Dimensity ' || (800 + (p.idx % 4) * 100)
            ELSE 'Snapdragon ' || (6 + (p.idx % 4)) || ' Gen ' || (1 + (p.idx % 2))
        END
        WHEN 6 THEN CASE
            WHEN p.category_id = 6 THEN 'iOS'
            WHEN p.category_id IN (1, 7, 8) THEN 'Android'
            WHEN p.category_id = 3 THEN 'Android'
            ELSE 'Windows'
        END
        WHEN 7 THEN CASE p.category_id
            WHEN 9 THEN 'Intel Core i5-' || (1135 + (p.idx % 6))
            WHEN 10 THEN 'AMD Ryzen ' || (5 + (p.idx % 2)) || ' 5' || (500 + (p.idx % 5) * 10)
            ELSE 'Intel Core i5-' || (10210 + p.idx)
        END
        WHEN 8 THEN CASE WHEN p.category_id IN (2, 9, 10) THEN 'Intel Iris Xe' ELSE 'Adreno ' || (620 + (p.idx % 4) * 20) END
        WHEN 9 THEN ((12 + p.idx)::numeric / 10)::text
        WHEN 10 THEN (ARRAY['Sac nhanh','Cap sac','Tai nghe','Ban phim','Chuot'])[1 + (p.idx % 5)]
        WHEN 11 THEN CASE p.category_id
            WHEN 5 THEN 'Da thiet bi'
            WHEN 4 THEN 'Android va iOS'
            WHEN 2 THEN 'Windows'
            WHEN 9 THEN 'Windows'
            WHEN 10 THEN 'Windows'
            ELSE 'Android va iOS'
        END
        WHEN 12 THEN (ARRAY['Den','Trang','Xam','Xanh duong','Hong'])[1 + (p.idx % 5)]
        WHEN 13 THEN (CASE WHEN p.category_id IN (2, 9, 10) THEN 24 ELSE 12 END)::text
        WHEN 14 THEN CASE WHEN p.category_id = 4 THEN '5ATM' ELSE 'IP68' END
        WHEN 15 THEN (ARRAY['Silicone','Da','Nylon'])[1 + (p.idx % 3)]
        WHEN 16 THEN CASE
            WHEN p.category_id = 5 THEN 'USB-C'
            WHEN p.category_id = 3 THEN 'WiFi, Bluetooth'
            ELSE 'Bluetooth 5.' || (p.idx % 3)
        END
        WHEN 17 THEN (12 + (p.idx % 6) * 12)::text
        ELSE 'N/A'
    END AS value
FROM seeded_products p
JOIN app_categoryattribute ca ON ca.category_id = p.category_id;

SELECT setval(pg_get_serial_sequence('app_attribute', 'id'), (SELECT GREATEST(MAX(id), 1) FROM app_attribute));
SELECT setval(pg_get_serial_sequence('app_categoryattribute', 'id'), (SELECT GREATEST(MAX(id), 1) FROM app_categoryattribute));
SELECT setval(pg_get_serial_sequence('app_productattributevalue', 'id'), (SELECT GREATEST(MAX(id), 1) FROM app_productattributevalue));
