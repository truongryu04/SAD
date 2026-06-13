-- Seed data for user_service_db
-- Run with: mysql -uroot -p123456 < mysql-init.sql/seed_user_service.sql

USE user_service_db;

SET FOREIGN_KEY_CHECKS = 0;
DELETE FROM `app_useractivity`;
DELETE FROM `app_rating`;
DELETE FROM `app_searchhistory`;
DELETE FROM `app_cartitem`;
DELETE FROM `app_cart`;
DELETE FROM `app_useraccount`;
SET FOREIGN_KEY_CHECKS = 1;

INSERT INTO `app_useraccount` (
  `id`, `username`, `full_name`, `password`, `role`, `is_active`, `created_at`
) VALUES
  (1, 'customer001', 'Khach hang 001', 'demo_password_hash', 'CUSTOMER', 1, '2026-05-01 09:00:00'),
  (2, 'customer002', 'Khach hang 002', 'demo_password_hash', 'CUSTOMER', 1, '2026-05-01 09:05:00'),
  (3, 'customer003', 'Khach hang 003', 'demo_password_hash', 'CUSTOMER', 1, '2026-05-01 09:10:00'),
  (4, 'customer004', 'Khach hang 004', 'demo_password_hash', 'CUSTOMER', 1, '2026-05-01 09:15:00'),
  (5, 'customer005', 'Khach hang 005', 'demo_password_hash', 'CUSTOMER', 1, '2026-05-01 09:20:00'),
  (6, 'customer006', 'Khach hang 006', 'demo_password_hash', 'CUSTOMER', 1, '2026-05-01 09:25:00'),
  (7, 'customer007', 'Khach hang 007', 'demo_password_hash', 'CUSTOMER', 1, '2026-05-01 09:30:00'),
  (8, 'customer008', 'Khach hang 008', 'demo_password_hash', 'CUSTOMER', 1, '2026-05-01 09:35:00'),
  (9, 'customer009', 'Khach hang 009', 'demo_password_hash', 'CUSTOMER', 1, '2026-05-01 09:40:00'),
  (10, 'customer010', 'Khach hang 010', 'demo_password_hash', 'CUSTOMER', 1, '2026-05-01 09:45:00'),
  (11, 'customer011', 'Khach hang 011', 'demo_password_hash', 'CUSTOMER', 1, '2026-05-01 09:50:00'),
  (12, 'customer012', 'Khach hang 012', 'demo_password_hash', 'CUSTOMER', 1, '2026-05-01 09:55:00'),
  (13, 'customer013', 'Khach hang 013', 'demo_password_hash', 'CUSTOMER', 1, '2026-05-01 10:00:00'),
  (14, 'customer014', 'Khach hang 014', 'demo_password_hash', 'CUSTOMER', 1, '2026-05-01 10:05:00'),
  (15, 'customer015', 'Khach hang 015', 'demo_password_hash', 'CUSTOMER', 1, '2026-05-01 10:10:00'),
  (16, 'admin001', 'Quan tri 001', 'demo_password_hash', 'ADMIN', 1, '2026-05-01 08:00:00'),
  (17, 'staff001', 'Nhan vien 001', 'demo_password_hash', 'STAFF', 1, '2026-05-01 08:05:00'),
  (18, 'admin', 'Administrator', 'pbkdf2_sha256$1000000$AmnPPp7bsTBFOvxfj3fUkq$uqKB7IDl5a4uqA2ZEGc8wSJaKMNQSii0Z3oN4NZD6lE=', 'ADMIN', 1, '2026-05-05 00:00:00');

INSERT INTO `app_cart` (`id`, `user_id`, `is_active`, `created_at`) VALUES
  (1, 1, 1, '2026-05-02 08:00:00'),
  (2, 2, 1, '2026-05-02 08:05:00'),
  (3, 3, 1, '2026-05-02 08:10:00'),
  (4, 4, 1, '2026-05-02 08:15:00'),
  (5, 5, 1, '2026-05-02 08:20:00'),
  (6, 6, 1, '2026-05-02 08:25:00'),
  (7, 7, 1, '2026-05-02 08:30:00'),
  (8, 8, 1, '2026-05-02 08:35:00'),
  (9, 9, 1, '2026-05-02 08:40:00'),
  (10, 10, 1, '2026-05-02 08:45:00');

INSERT INTO `app_cartitem` (`id`, `cart_id`, `item_type`, `item_id`, `quantity`) VALUES
  (1, 1, 'product', 25, 1),
  (2, 1, 'product', 8, 1),
  (3, 2, 'product', 26, 1),
  (4, 2, 'product', 7, 1),
  (5, 3, 'product', 27, 1),
  (6, 3, 'product', 5, 1),
  (7, 4, 'product', 21, 1),
  (8, 4, 'product', 11, 1),
  (9, 5, 'product', 24, 1),
  (10, 5, 'product', 10, 1),
  (11, 6, 'product', 30, 1),
  (12, 6, 'product', 29, 1),
  (13, 7, 'product', 15, 1),
  (14, 7, 'product', 2, 1),
  (15, 8, 'product', 34, 2),
  (16, 8, 'product', 38, 1),
  (17, 9, 'product', 32, 1),
  (18, 9, 'product', 31, 1),
  (19, 10, 'product', 28, 1),
  (20, 10, 'product', 12, 1);

INSERT INTO `app_searchhistory` (`id`, `user_id`, `keyword`, `created_at`) VALUES
  (1, 1, 'iphone 15', '2026-05-03 09:00:00'),
  (2, 2, 'samsung galaxy s24', '2026-05-03 09:05:00'),
  (3, 3, 'xiaomi redmi note 13 pro', '2026-05-03 09:10:00'),
  (4, 4, 'macbook air m3', '2026-05-03 09:15:00'),
  (5, 5, 'asus vivobook 15', '2026-05-03 09:20:00'),
  (6, 6, 'robot vacuum', '2026-05-03 09:25:00');

INSERT INTO `app_rating` (
  `id`, `user_id`, `item_type`, `item_id`, `score`, `review`, `created_at`, `updated_at`
) VALUES
  (1, 1, 'mobile', 25, 5, 'May dep, camera tot', '2026-05-03 10:00:00', '2026-05-03 10:00:00'),
  (2, 2, 'mobile', 26, 4, 'Hieu nang manh, cam giac cao cap', '2026-05-03 10:05:00', '2026-05-03 10:05:00'),
  (3, 3, 'mobile', 27, 4, 'Gia/hiieu nang on', '2026-05-03 10:10:00', '2026-05-03 10:10:00'),
  (4, 4, 'laptop', 21, 5, 'May nhe, pin tot', '2026-05-03 10:15:00', '2026-05-03 10:15:00');

INSERT INTO `app_useractivity` (
  `id`, `user_id`, `action`, `item_type`, `item_id`, `quantity`, `rating_score`, `metadata`, `created_at`
) VALUES
  (1, 1, 'VIEW_PRODUCT', 'product', 25, 0, NULL, JSON_OBJECT('source', 'seed', 'channel', 'web'), '2026-05-03 08:00:00'),
  (2, 1, 'ADD_TO_CART', 'product', 8, 1, NULL, JSON_OBJECT('source', 'seed', 'channel', 'web'), '2026-05-03 08:03:00'),
  (3, 1, 'RATE_PRODUCT', 'mobile', 25, 0, 5, JSON_OBJECT('source', 'seed', 'channel', 'web'), '2026-05-03 10:00:00'),
  (4, 2, 'VIEW_PRODUCT', 'product', 26, 0, NULL, JSON_OBJECT('source', 'seed', 'channel', 'app'), '2026-05-03 08:10:00'),
  (5, 2, 'ADD_TO_CART', 'product', 7, 1, NULL, JSON_OBJECT('source', 'seed', 'channel', 'app'), '2026-05-03 08:12:00'),
  (6, 2, 'RATE_PRODUCT', 'mobile', 26, 0, 4, JSON_OBJECT('source', 'seed', 'channel', 'app'), '2026-05-03 10:05:00');
