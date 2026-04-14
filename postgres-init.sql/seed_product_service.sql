-- Seed data for product_service_db (PostgreSQL)
-- Run on product_service_db

TRUNCATE TABLE app_productvariant, app_product RESTART IDENTITY;

INSERT INTO app_product (
    id, name, description, category_id, brand, base_price, status, created_at, updated_at
)
WITH product_seed AS (
    SELECT
        g AS id,
        ((g - 1) / 10) + 1 AS category_id,
        ((g - 1) % 10) + 1 AS idx
    FROM generate_series(1, 100) AS g
)
SELECT
    p.id,
    CASE p.category_id
        WHEN 1 THEN 'Realme C' || (30 + p.idx)
        WHEN 2 THEN 'Acer Aspire ' || (3 + p.idx)
        WHEN 3 THEN 'Lenovo Tab M' || (8 + (p.idx % 4)) || ' Gen ' || (1 + (p.idx % 3))
        WHEN 4 THEN 'Garmin Venu ' || (2 + (p.idx % 3)) || ' Sport'
        WHEN 5 THEN (ARRAY['Sac nhanh 33W','Sac nhanh 65W','Cap USB-C 1m','Tai nghe TWS','Op lung chong soc','Pin du phong 10000mAh','Ban phim Bluetooth','Chuot khong day','Gia do dien thoai','Tai nghe choang on'])[p.idx]
        WHEN 6 THEN 'iPhone ' || (13 + (p.idx % 4)) || CASE WHEN p.idx % 3 = 0 THEN ' Pro' ELSE '' END
        WHEN 7 THEN 'Galaxy S' || (22 + (p.idx % 4)) || CASE WHEN p.idx % 3 = 0 THEN ' Ultra' ELSE '' END
        WHEN 8 THEN 'Xiaomi Redmi Note ' || (11 + (p.idx % 5))
        WHEN 9 THEN 'Dell Inspiron ' || (3500 + p.idx * 3)
        ELSE 'ASUS VivoBook ' || (14 + (p.idx % 2)) || 'X'
    END,
    CASE p.category_id
        WHEN 1 THEN 'Dien thoai Android pho thong, pin tot, man hinh lon.'
        WHEN 2 THEN 'Laptop van phong da dung cho hoc tap va cong viec.'
        WHEN 3 THEN 'May tinh bang hoc tap va giai tri voi man hinh lon.'
        WHEN 4 THEN 'Dong ho thong minh theo doi suc khoe va van dong.'
        WHEN 5 THEN 'Phu kien cong nghe chinh hang, tuong thich da thiet bi.'
        WHEN 6 THEN 'iPhone chinh hang voi hieu nang manh, camera tot.'
        WHEN 7 THEN 'Flagship Samsung voi man hinh AMOLED va camera cao cap.'
        WHEN 8 THEN 'Xiaomi tam trung cau hinh cao trong tam gia.'
        WHEN 9 THEN 'Laptop Dell ben bi, toi uu cho van phong va doanh nghiep.'
        ELSE 'Laptop ASUS gon nhe, can bang hieu nang va tinh di dong.'
    END,
    p.category_id,
    CASE p.category_id
        WHEN 1 THEN 'Realme'
        WHEN 2 THEN 'Acer'
        WHEN 3 THEN 'Lenovo'
        WHEN 4 THEN 'Garmin'
        WHEN 5 THEN 'Anker'
        WHEN 6 THEN 'Apple'
        WHEN 7 THEN 'Samsung'
        WHEN 8 THEN 'Xiaomi'
        WHEN 9 THEN 'Dell'
        ELSE 'ASUS'
    END,
    CASE p.category_id
        WHEN 1 THEN (3200000 + p.idx * 550000)::numeric(12,2)
        WHEN 2 THEN (11500000 + p.idx * 1500000)::numeric(12,2)
        WHEN 3 THEN (5900000 + p.idx * 900000)::numeric(12,2)
        WHEN 4 THEN (2800000 + p.idx * 600000)::numeric(12,2)
        WHEN 5 THEN (150000 + p.idx * 180000)::numeric(12,2)
        WHEN 6 THEN (18900000 + p.idx * 2200000)::numeric(12,2)
        WHEN 7 THEN (9900000 + p.idx * 2000000)::numeric(12,2)
        WHEN 8 THEN (4500000 + p.idx * 1100000)::numeric(12,2)
        WHEN 9 THEN (13900000 + p.idx * 1800000)::numeric(12,2)
        ELSE (12900000 + p.idx * 1700000)::numeric(12,2)
    END,
    CASE WHEN p.idx = 10 THEN 'INACTIVE' ELSE 'ACTIVE' END,
    NOW() - (p.id || ' days')::interval,
    NOW() - (p.id || ' hours')::interval
FROM product_seed p;

INSERT INTO app_productvariant (
    id, product_id, sku, price, status, created_at
)
SELECT
    ROW_NUMBER() OVER (ORDER BY p.id, v.n),
    p.id,
    'SKU-' || lpad(p.id::text, 4, '0') || '-' || v.n,
    (p.base_price * (CASE WHEN v.n = 1 THEN 1.00 ELSE 1.08 END))::numeric(12,2),
    CASE WHEN p.status = 'INACTIVE' THEN 'INACTIVE' ELSE 'ACTIVE' END,
    NOW() - ((p.id + v.n) || ' days')::interval
FROM app_product p
CROSS JOIN generate_series(1, 2) AS v(n);

SELECT setval(pg_get_serial_sequence('app_product', 'id'), (SELECT GREATEST(MAX(id), 1) FROM app_product));
SELECT setval(pg_get_serial_sequence('app_productvariant', 'id'), (SELECT GREATEST(MAX(id), 1) FROM app_productvariant));
