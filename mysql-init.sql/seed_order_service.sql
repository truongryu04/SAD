-- Seed data for order_service_db (20 orders dataset)
-- Run with: mysql -uroot -p123456 < mysql-init.sql/seed_order_service.sql

USE order_service_db;

SET FOREIGN_KEY_CHECKS = 0;
DELETE FROM `app_orderitem`;
DELETE FROM `app_order`;
SET FOREIGN_KEY_CHECKS = 1;

INSERT INTO `app_order` (
  `id`, `customer_id`, `cart_id`, `payment_method`, `payment_status`, `order_status`, `total_amount`, `created_at`
) VALUES
  (1, 1, NULL, 'CARD', 'PAID', 'CONFIRMED', 23480000.00, '2026-05-03 11:00:00'),
  (2, 2, NULL, 'VNPAY', 'PAID', 'CONFIRMED', 22480000.00, '2026-05-03 11:10:00'),
  (3, 3, NULL, 'MOMO', 'PAID', 'CONFIRMED', 10980000.00, '2026-05-03 11:20:00'),
  (4, 4, NULL, 'CARD', 'PAID', 'CONFIRMED', 29239000.00, '2026-05-03 11:30:00'),
  (5, 5, NULL, 'COD', 'PENDING', 'CREATED', 16189000.00, '2026-05-03 11:40:00'),
  (6, 6, NULL, 'VNPAY', 'PAID', 'CONFIRMED', 11180000.00, '2026-05-03 11:50:00'),
  (7, 7, NULL, 'MOMO', 'PAID', 'CONFIRMED', 1739000.00, '2026-05-03 12:00:00'),
  (8, 8, NULL, 'CARD', 'PAID', 'CONFIRMED', 2097000.00, '2026-05-03 12:10:00'),
  (9, 9, NULL, 'COD', 'FAILED', 'CANCELLED', 15580000.00, '2026-05-03 12:20:00'),
  (10, 10, NULL, 'CARD', 'PAID', 'CONFIRMED', 18339000.00, '2026-05-03 12:30:00'),
  (11, 11, NULL, 'MOMO', 'PAID', 'CONFIRMED', 740000.00, '2026-05-03 12:40:00'),
  (12, 12, NULL, 'VNPAY', 'PAID', 'CONFIRMED', 839000.00, '2026-05-03 12:50:00'),
  (13, 13, NULL, 'CARD', 'PAID', 'CONFIRMED', 38480000.00, '2026-05-03 13:00:00'),
  (14, 14, NULL, 'VNPAY', 'PAID', 'CONFIRMED', 41480000.00, '2026-05-03 13:10:00'),
  (15, 15, NULL, 'COD', 'PENDING', 'CREATED', 2788000.00, '2026-05-03 13:20:00'),
  (16, 1, NULL, 'CARD', 'PAID', 'CONFIRMED', 1598000.00, '2026-05-04 09:00:00'),
  (17, 2, NULL, 'MOMO', 'PAID', 'CONFIRMED', 3970000.00, '2026-05-04 09:10:00'),
  (18, 3, NULL, 'VNPAY', 'PAID', 'CONFIRMED', 3038000.00, '2026-05-04 09:20:00'),
  (19, 4, NULL, 'CARD', 'PAID', 'CONFIRMED', 574000.00, '2026-05-04 09:30:00'),
  (20, 5, NULL, 'COD', 'PENDING', 'CREATED', 2098000.00, '2026-05-04 09:40:00');

INSERT INTO `app_orderitem` (
  `id`, `order_id`, `item_type`, `item_id`, `item_name`, `quantity`, `unit_price`, `line_total`
) VALUES
  (1, 1, 'product', 25, 'iPhone 15', 1, 22990000.00, 22990000.00),
  (2, 1, 'product', 8, 'Anker PowerCore 10000mAh', 1, 490000.00, 490000.00),

  (3, 2, 'product', 26, 'Samsung Galaxy S24', 1, 20990000.00, 20990000.00),
  (4, 2, 'product', 7, 'TP-Link Archer AX55 Wi-Fi 6 Router', 1, 1490000.00, 1490000.00),

  (5, 3, 'product', 27, 'Xiaomi Redmi Note 13 Pro', 1, 7990000.00, 7990000.00),
  (6, 3, 'product', 5, 'JBL Flip 6 Bluetooth Speaker', 1, 2990000.00, 2990000.00),

  (7, 4, 'product', 21, 'MacBook Air M3 13-inch', 1, 28990000.00, 28990000.00),
  (8, 4, 'product', 11, 'Leather Belt Premium', 1, 249000.00, 249000.00),

  (9, 5, 'product', 24, 'ASUS VivoBook 15', 1, 15990000.00, 15990000.00),
  (10, 5, 'product', 10, 'Baseball Cap Classic', 1, 199000.00, 199000.00),

  (11, 6, 'product', 30, 'Xiaomi Robot Vacuum S10+', 1, 8990000.00, 8990000.00),
  (12, 6, 'product', 29, 'Philips Air Fryer 4.1L', 1, 2190000.00, 2190000.00),

  (13, 7, 'product', 15, 'Introduction to Algorithms (CLRS)', 1, 890000.00, 890000.00),
  (14, 7, 'product', 2, 'Clean Code', 1, 350000.00, 350000.00),
  (15, 7, 'product', 9, 'Unisex Hoodie Basic', 1, 499000.00, 499000.00),

  (16, 8, 'product', 34, 'Men''s Slim Jeans', 2, 499000.00, 998000.00),
  (17, 8, 'product', 38, 'Sneakers Court Classic', 1, 1099000.00, 1099000.00),

  (18, 9, 'product', 32, 'LG Front Load Washer 9kg', 1, 12990000.00, 12990000.00),
  (19, 9, 'product', 31, 'Panasonic Microwave 23L', 1, 2590000.00, 2590000.00),

  (20, 10, 'product', 28, 'Google Pixel 8', 1, 17990000.00, 17990000.00),
  (21, 10, 'product', 12, 'Sunglasses UV400', 1, 349000.00, 349000.00),

  (22, 11, 'product', 1, 'The Pragmatic Programmer', 1, 320000.00, 320000.00),
  (23, 11, 'product', 3, 'Design Patterns', 1, 420000.00, 420000.00),

  (24, 12, 'product', 17, 'Norwegian Wood', 2, 220000.00, 440000.00),
  (25, 12, 'product', 40, 'Sandals Comfort', 1, 399000.00, 399000.00),

  (26, 13, 'product', 22, 'Dell XPS 13 (2024)', 1, 32990000.00, 32990000.00),
  (27, 13, 'product', 6, 'Apple Watch SE (2024)', 1, 5490000.00, 5490000.00),

  (28, 14, 'product', 23, 'Lenovo ThinkPad X1 Carbon Gen 12', 1, 39990000.00, 39990000.00),
  (29, 14, 'product', 7, 'TP-Link Archer AX55 Wi-Fi 6 Router', 1, 1490000.00, 1490000.00),

  (30, 15, 'product', 29, 'Philips Air Fryer 4.1L', 1, 2190000.00, 2190000.00),
  (31, 15, 'product', 33, 'Men''s Polo Shirt', 2, 299000.00, 598000.00),

  (32, 16, 'product', 39, 'Leather Loafers', 1, 1199000.00, 1199000.00),
  (33, 16, 'product', 35, 'Men''s Formal Shirt', 1, 399000.00, 399000.00),

  (34, 17, 'product', 8, 'Anker PowerCore 10000mAh', 2, 490000.00, 980000.00),
  (35, 17, 'product', 5, 'JBL Flip 6 Bluetooth Speaker', 1, 2990000.00, 2990000.00),

  (36, 18, 'product', 31, 'Panasonic Microwave 23L', 1, 2590000.00, 2590000.00),
  (37, 18, 'product', 10, 'Baseball Cap Classic', 1, 199000.00, 199000.00),
  (38, 18, 'product', 11, 'Leather Belt Premium', 1, 249000.00, 249000.00),

  (39, 19, 'product', 18, 'The Alchemist', 1, 189000.00, 189000.00),
  (40, 19, 'product', 19, '1984', 1, 210000.00, 210000.00),
  (41, 19, 'product', 20, 'The Little Prince', 1, 175000.00, 175000.00),

  (42, 20, 'product', 37, 'Running Shoes Air Zoom', 1, 1299000.00, 1299000.00),
  (43, 20, 'product', 36, 'Men''s Bomber Jacket', 1, 799000.00, 799000.00);
