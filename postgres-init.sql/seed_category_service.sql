-- Seed data for category_service_db (PostgreSQL)
-- Run on category_service_db

TRUNCATE TABLE app_category RESTART IDENTITY;

INSERT INTO app_category (
    id, name, description, parent_id, status, created_at, updated_at
)
VALUES
    (1, 'Dien thoai', 'Danh muc dien thoai thong minh', NULL, 'ACTIVE', NOW() - INTERVAL '20 days', NOW() - INTERVAL '1 hours'),
    (2, 'Laptop', 'Danh muc laptop van phong va gaming', NULL, 'ACTIVE', NOW() - INTERVAL '20 days', NOW() - INTERVAL '1 hours'),
    (3, 'May tinh bang', 'Danh muc tablet hoc tap va giai tri', NULL, 'ACTIVE', NOW() - INTERVAL '18 days', NOW() - INTERVAL '1 hours'),
    (4, 'Dong ho thong minh', 'Dong ho thong minh theo doi suc khoe', NULL, 'ACTIVE', NOW() - INTERVAL '18 days', NOW() - INTERVAL '1 hours'),
    (5, 'Phu kien cong nghe', 'Phu kien nhu sac, cap, op lung, chuot', NULL, 'ACTIVE', NOW() - INTERVAL '16 days', NOW() - INTERVAL '1 hours'),
    (6, 'Apple', 'San pham thuong hieu Apple', 1, 'ACTIVE', NOW() - INTERVAL '14 days', NOW() - INTERVAL '1 hours'),
    (7, 'Samsung', 'San pham thuong hieu Samsung', 1, 'ACTIVE', NOW() - INTERVAL '14 days', NOW() - INTERVAL '1 hours'),
    (8, 'Xiaomi', 'San pham thuong hieu Xiaomi', 1, 'ACTIVE', NOW() - INTERVAL '12 days', NOW() - INTERVAL '1 hours'),
    (9, 'Dell', 'San pham thuong hieu Dell', 2, 'ACTIVE', NOW() - INTERVAL '12 days', NOW() - INTERVAL '1 hours'),
    (10, 'ASUS', 'San pham thuong hieu ASUS', 2, 'ACTIVE', NOW() - INTERVAL '10 days', NOW() - INTERVAL '1 hours');

SELECT setval(pg_get_serial_sequence('app_category', 'id'), (SELECT GREATEST(MAX(id), 1) FROM app_category));
