-- Seed data for staff_service_db
-- Run with: mysql -uroot -p123456 < mysql-init.sql/seed_staff_service.sql

USE staff_service_db;

INSERT INTO `app_staffaccount` (
  `id`, `username`, `full_name`, `password`, `role`, `is_active`, `created_at`
)
WITH RECURSIVE seq AS (
  SELECT 1 AS n
  UNION ALL
  SELECT n + 1 FROM seq WHERE n < 50
)
SELECT
  n,
  CONCAT('staff', LPAD(n, 3, '0')),
  CONCAT('Nhan vien ', LPAD(n, 3, '0')),
  'demo_password_hash',
  'STAFF',
  IF(n % 13 = 0, 0, 1),
  DATE_SUB(NOW(), INTERVAL n DAY)
FROM seq
ON DUPLICATE KEY UPDATE
  `full_name` = VALUES(`full_name`),
  `is_active` = VALUES(`is_active`);
