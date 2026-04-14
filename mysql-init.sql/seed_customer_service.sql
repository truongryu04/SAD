-- Seed data for customer_service_db (10 customers dataset)
-- Run with: mysql -uroot -p123456 < mysql-init.sql/seed_customer_service.sql

USE customer_service_db;

SET FOREIGN_KEY_CHECKS = 0;
DELETE FROM `app_useractivity`;
DELETE FROM `app_rating`;
DELETE FROM `app_searchhistory`;
DELETE FROM `app_cartitem`;
DELETE FROM `app_cart`;
DELETE FROM `app_customeraccount`;
SET FOREIGN_KEY_CHECKS = 1;

INSERT INTO `app_customeraccount` (
  `id`, `username`, `full_name`, `password`, `role`, `is_active`, `created_at`
) VALUES
  (1, 'customer001', 'Khach hang 001', 'demo_password_hash', 'CUSTOMER', 1, '2026-03-01 09:00:00'),
  (2, 'customer002', 'Khach hang 002', 'demo_password_hash', 'CUSTOMER', 1, '2026-03-02 09:00:00'),
  (3, 'customer003', 'Khach hang 003', 'demo_password_hash', 'CUSTOMER', 1, '2026-03-03 09:00:00'),
  (4, 'customer004', 'Khach hang 004', 'demo_password_hash', 'CUSTOMER', 1, '2026-03-04 09:00:00'),
  (5, 'customer005', 'Khach hang 005', 'demo_password_hash', 'CUSTOMER', 1, '2026-03-05 09:00:00'),
  (6, 'customer006', 'Khach hang 006', 'demo_password_hash', 'CUSTOMER', 1, '2026-03-06 09:00:00'),
  (7, 'customer007', 'Khach hang 007', 'demo_password_hash', 'CUSTOMER', 1, '2026-03-07 09:00:00'),
  (8, 'customer008', 'Khach hang 008', 'demo_password_hash', 'CUSTOMER', 1, '2026-03-08 09:00:00'),
  (9, 'customer009', 'Khach hang 009', 'demo_password_hash', 'CUSTOMER', 1, '2026-03-09 09:00:00'),
  (10, 'customer010', 'Khach hang 010', 'demo_password_hash', 'CUSTOMER', 1, '2026-03-10 09:00:00');

INSERT INTO `app_cart` (`id`, `customer_id`, `is_active`, `created_at`) VALUES
  (1, 1, 1, '2026-03-20 08:00:00'),
  (2, 2, 1, '2026-03-20 08:05:00'),
  (3, 3, 1, '2026-03-20 08:10:00'),
  (4, 4, 1, '2026-03-20 08:15:00'),
  (5, 5, 1, '2026-03-20 08:20:00'),
  (6, 6, 1, '2026-03-20 08:25:00'),
  (7, 7, 1, '2026-03-20 08:30:00'),
  (8, 8, 1, '2026-03-20 08:35:00'),
  (9, 9, 1, '2026-03-20 08:40:00'),
  (10, 10, 1, '2026-03-20 08:45:00');

INSERT INTO `app_cartitem` (`id`, `cart_id`, `item_type`, `item_id`, `quantity`) VALUES
  (1, 1, 'product', 6, 1),
  (2, 1, 'product', 22, 1),
  (3, 1, 'product', 5, 1),
  (4, 2, 'product', 57, 1),
  (5, 2, 'product', 73, 1),
  (6, 2, 'product', 11, 2),
  (7, 3, 'product', 14, 1),
  (8, 3, 'product', 9, 1),
  (9, 3, 'product', 33, 1),
  (10, 4, 'product', 71, 1),
  (11, 4, 'product', 3, 2),
  (12, 4, 'product', 2, 1),
  (13, 5, 'product', 48, 1),
  (14, 5, 'product', 16, 1),
  (15, 5, 'product', 89, 1),
  (16, 6, 'product', 10, 1),
  (17, 6, 'product', 36, 1),
  (18, 6, 'product', 52, 1),
  (19, 7, 'product', 77, 1),
  (20, 7, 'product', 24, 1),
  (21, 7, 'product', 4, 1),
  (22, 8, 'product', 30, 1),
  (23, 8, 'product', 68, 1),
  (24, 8, 'product', 66, 1),
  (25, 9, 'product', 18, 1),
  (26, 9, 'product', 95, 1),
  (27, 9, 'product', 41, 1),
  (28, 10, 'product', 25, 1),
  (29, 10, 'product', 8, 1),
  (30, 10, 'product', 73, 1);

INSERT INTO `app_searchhistory` (`id`, `customer_id`, `keyword`, `created_at`) VALUES
  (1, 1, 'iphone 15', '2026-03-25 09:00:00'),
  (2, 1, 'sac nhanh 65w', '2026-03-25 09:05:00'),
  (3, 2, 'samsung galaxy', '2026-03-25 09:10:00'),
  (4, 2, 'tai nghe bluetooth', '2026-03-25 09:20:00'),
  (5, 3, 'macbook air', '2026-03-25 09:25:00'),
  (6, 3, 'chuot khong day', '2026-03-25 09:35:00'),
  (7, 4, 'xiaomi redmi', '2026-03-25 09:40:00'),
  (8, 4, 'op lung chong soc', '2026-03-25 09:45:00'),
  (9, 5, 'asus vivobook', '2026-03-25 10:00:00'),
  (10, 5, 'pin du phong', '2026-03-25 10:10:00'),
  (11, 6, 'dell inspiron', '2026-03-25 10:20:00'),
  (12, 6, 'ban phim bluetooth', '2026-03-25 10:25:00'),
  (13, 7, 'realme gt neo', '2026-03-25 10:30:00'),
  (14, 7, 'cap usb c', '2026-03-25 10:35:00'),
  (15, 8, 'galaxy a55', '2026-03-25 10:40:00'),
  (16, 8, 'sac nhanh 33w', '2026-03-25 10:45:00'),
  (17, 9, 'laptop gaming', '2026-03-25 10:50:00'),
  (18, 9, 'balo laptop', '2026-03-25 10:55:00'),
  (19, 10, 'iphone 14', '2026-03-25 11:00:00'),
  (20, 10, 'xiaomi redmi note 11', '2026-03-25 11:05:00');

INSERT INTO `app_rating` (
  `id`, `customer_id`, `item_type`, `item_id`, `score`, `review`, `created_at`, `updated_at`
) VALUES
  (1, 1, 'mobile', 6, 5, 'May dung on dinh va pin tot', '2026-03-26 09:00:00', '2026-03-26 09:00:00'),
  (2, 2, 'mobile', 57, 4, 'Hieu nang tot trong tam gia', '2026-03-26 09:05:00', '2026-03-26 09:05:00'),
  (3, 3, 'laptop', 14, 5, 'Man hinh dep va pin trau', '2026-03-26 09:10:00', '2026-03-26 09:10:00'),
  (4, 4, 'mobile', 71, 4, 'May on trong nhom gia re', '2026-03-26 09:15:00', '2026-03-26 09:15:00'),
  (5, 5, 'laptop', 48, 4, 'Phu hop hoc tap van phong', '2026-03-26 09:20:00', '2026-03-26 09:20:00'),
  (6, 6, 'laptop', 10, 3, 'Tam on, can nang cap RAM', '2026-03-26 09:25:00', '2026-03-26 09:25:00'),
  (7, 7, 'mobile', 77, 4, 'Gia hop ly, camera du dung', '2026-03-26 09:30:00', '2026-03-26 09:30:00'),
  (8, 8, 'laptop', 30, 5, 'Build chac chan, ban phim tot', '2026-03-26 09:35:00', '2026-03-26 09:35:00'),
  (9, 9, 'laptop', 18, 5, 'Hieu nang manh cho cong viec', '2026-03-26 09:40:00', '2026-03-26 09:40:00'),
  (10, 10, 'mobile', 8, 4, 'Nho gon, de dung hang ngay', '2026-03-26 09:45:00', '2026-03-26 09:45:00');

INSERT INTO `app_useractivity` (
  `id`, `customer_id`, `action`, `item_type`, `item_id`, `quantity`, `rating_score`, `metadata`, `created_at`
) VALUES
  (1, 1, 'VIEW_PRODUCT', 'product', 6, 0, NULL, JSON_OBJECT('source', 'seed', 'channel', 'web'), '2026-03-24 08:00:00'),
  (2, 1, 'ADD_TO_CART', 'product', 22, 1, NULL, JSON_OBJECT('source', 'seed', 'channel', 'web'), '2026-03-24 08:05:00'),
  (3, 1, 'RATE_PRODUCT', 'mobile', 6, 0, 5, JSON_OBJECT('source', 'seed', 'channel', 'web'), '2026-03-26 09:00:00'),
  (4, 2, 'VIEW_PRODUCT', 'product', 57, 0, NULL, JSON_OBJECT('source', 'seed', 'channel', 'app'), '2026-03-24 08:10:00'),
  (5, 2, 'ADD_TO_CART', 'product', 73, 1, NULL, JSON_OBJECT('source', 'seed', 'channel', 'app'), '2026-03-24 08:15:00'),
  (6, 2, 'RATE_PRODUCT', 'mobile', 57, 0, 4, JSON_OBJECT('source', 'seed', 'channel', 'app'), '2026-03-26 09:05:00'),
  (7, 3, 'VIEW_PRODUCT', 'product', 14, 0, NULL, JSON_OBJECT('source', 'seed', 'channel', 'web'), '2026-03-24 08:20:00'),
  (8, 3, 'ADD_TO_CART', 'product', 9, 1, NULL, JSON_OBJECT('source', 'seed', 'channel', 'web'), '2026-03-24 08:25:00'),
  (9, 3, 'RATE_PRODUCT', 'laptop', 14, 0, 5, JSON_OBJECT('source', 'seed', 'channel', 'web'), '2026-03-26 09:10:00'),
  (10, 4, 'VIEW_PRODUCT', 'product', 71, 0, NULL, JSON_OBJECT('source', 'seed', 'channel', 'app'), '2026-03-24 08:30:00'),
  (11, 4, 'ADD_TO_CART', 'product', 3, 2, NULL, JSON_OBJECT('source', 'seed', 'channel', 'app'), '2026-03-24 08:35:00'),
  (12, 4, 'RATE_PRODUCT', 'mobile', 71, 0, 4, JSON_OBJECT('source', 'seed', 'channel', 'app'), '2026-03-26 09:15:00'),
  (13, 5, 'VIEW_PRODUCT', 'product', 48, 0, NULL, JSON_OBJECT('source', 'seed', 'channel', 'web'), '2026-03-24 08:40:00'),
  (14, 5, 'ADD_TO_CART', 'product', 16, 1, NULL, JSON_OBJECT('source', 'seed', 'channel', 'web'), '2026-03-24 08:45:00'),
  (15, 5, 'RATE_PRODUCT', 'laptop', 48, 0, 4, JSON_OBJECT('source', 'seed', 'channel', 'web'), '2026-03-26 09:20:00'),
  (16, 6, 'VIEW_PRODUCT', 'product', 10, 0, NULL, JSON_OBJECT('source', 'seed', 'channel', 'app'), '2026-03-24 08:50:00'),
  (17, 6, 'ADD_TO_CART', 'product', 36, 1, NULL, JSON_OBJECT('source', 'seed', 'channel', 'app'), '2026-03-24 08:55:00'),
  (18, 6, 'RATE_PRODUCT', 'laptop', 10, 0, 3, JSON_OBJECT('source', 'seed', 'channel', 'app'), '2026-03-26 09:25:00'),
  (19, 7, 'VIEW_PRODUCT', 'product', 77, 0, NULL, JSON_OBJECT('source', 'seed', 'channel', 'web'), '2026-03-24 09:00:00'),
  (20, 7, 'ADD_TO_CART', 'product', 24, 1, NULL, JSON_OBJECT('source', 'seed', 'channel', 'web'), '2026-03-24 09:05:00'),
  (21, 7, 'RATE_PRODUCT', 'mobile', 77, 0, 4, JSON_OBJECT('source', 'seed', 'channel', 'web'), '2026-03-26 09:30:00'),
  (22, 8, 'VIEW_PRODUCT', 'product', 30, 0, NULL, JSON_OBJECT('source', 'seed', 'channel', 'app'), '2026-03-24 09:10:00'),
  (23, 8, 'ADD_TO_CART', 'product', 68, 1, NULL, JSON_OBJECT('source', 'seed', 'channel', 'app'), '2026-03-24 09:15:00'),
  (24, 8, 'RATE_PRODUCT', 'laptop', 30, 0, 5, JSON_OBJECT('source', 'seed', 'channel', 'app'), '2026-03-26 09:35:00'),
  (25, 9, 'VIEW_PRODUCT', 'product', 18, 0, NULL, JSON_OBJECT('source', 'seed', 'channel', 'web'), '2026-03-24 09:20:00'),
  (26, 9, 'ADD_TO_CART', 'product', 95, 1, NULL, JSON_OBJECT('source', 'seed', 'channel', 'web'), '2026-03-24 09:25:00'),
  (27, 9, 'RATE_PRODUCT', 'laptop', 18, 0, 5, JSON_OBJECT('source', 'seed', 'channel', 'web'), '2026-03-26 09:40:00'),
  (28, 10, 'VIEW_PRODUCT', 'product', 8, 0, NULL, JSON_OBJECT('source', 'seed', 'channel', 'app'), '2026-03-24 09:30:00'),
  (29, 10, 'ADD_TO_CART', 'product', 73, 1, NULL, JSON_OBJECT('source', 'seed', 'channel', 'app'), '2026-03-24 09:35:00'),
  (30, 10, 'RATE_PRODUCT', 'mobile', 8, 0, 4, JSON_OBJECT('source', 'seed', 'channel', 'app'), '2026-03-26 09:45:00');
