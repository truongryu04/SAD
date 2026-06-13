-- Seed data for product_service_db products (requested categories)
-- Run on product_service_db

TRUNCATE TABLE app_book RESTART IDENTITY CASCADE;
TRUNCATE TABLE app_electronics RESTART IDENTITY CASCADE;
TRUNCATE TABLE app_fashion RESTART IDENTITY CASCADE;
TRUNCATE TABLE app_product RESTART IDENTITY CASCADE;

-- 10 categories x 4 products = 40 products (3-5 per category requirement satisfied)
INSERT INTO app_product (
  id, name, price, stock, category_id, product_type, created_at, updated_at
) VALUES
  -- Book
  (1, 'The Pragmatic Programmer', 320000, 40, 1, 'BOOK', TIMESTAMPTZ '2026-05-04 08:00:00+00', TIMESTAMPTZ '2026-05-04 08:00:00+00'),
  (2, 'Clean Code', 350000, 35, 1, 'BOOK', TIMESTAMPTZ '2026-05-04 08:01:00+00', TIMESTAMPTZ '2026-05-04 08:01:00+00'),
  (3, 'Design Patterns', 420000, 25, 1, 'BOOK', TIMESTAMPTZ '2026-05-04 08:02:00+00', TIMESTAMPTZ '2026-05-04 08:02:00+00'),
  (4, 'Deep Learning with Python', 450000, 18, 1, 'BOOK', TIMESTAMPTZ '2026-05-04 08:03:00+00', TIMESTAMPTZ '2026-05-04 08:03:00+00'),

  -- Electronics
  (5, 'JBL Flip 6 Bluetooth Speaker', 2990000, 22, 2, 'ELECTRONICS', TIMESTAMPTZ '2026-05-04 08:04:00+00', TIMESTAMPTZ '2026-05-04 08:04:00+00'),
  (6, 'Apple Watch SE (2024)', 5490000, 16, 2, 'ELECTRONICS', TIMESTAMPTZ '2026-05-04 08:05:00+00', TIMESTAMPTZ '2026-05-04 08:05:00+00'),
  (7, 'TP-Link Archer AX55 Wi-Fi 6 Router', 1490000, 30, 2, 'ELECTRONICS', TIMESTAMPTZ '2026-05-04 08:06:00+00', TIMESTAMPTZ '2026-05-04 08:06:00+00'),
  (8, 'Anker PowerCore 10000mAh', 490000, 55, 2, 'ELECTRONICS', TIMESTAMPTZ '2026-05-04 08:07:00+00', TIMESTAMPTZ '2026-05-04 08:07:00+00'),

  -- Fashion
  (9, 'Unisex Hoodie Basic', 499000, 45, 3, 'FASHION', TIMESTAMPTZ '2026-05-04 08:08:00+00', TIMESTAMPTZ '2026-05-04 08:08:00+00'),
  (10, 'Baseball Cap Classic', 199000, 80, 3, 'FASHION', TIMESTAMPTZ '2026-05-04 08:09:00+00', TIMESTAMPTZ '2026-05-04 08:09:00+00'),
  (11, 'Leather Belt Premium', 249000, 60, 3, 'FASHION', TIMESTAMPTZ '2026-05-04 08:10:00+00', TIMESTAMPTZ '2026-05-04 08:10:00+00'),
  (12, 'Sunglasses UV400', 349000, 70, 3, 'FASHION', TIMESTAMPTZ '2026-05-04 08:11:00+00', TIMESTAMPTZ '2026-05-04 08:11:00+00'),

  -- Textbook
  (13, 'Calculus: Early Transcendentals', 520000, 20, 4, 'BOOK', TIMESTAMPTZ '2026-05-04 08:12:00+00', TIMESTAMPTZ '2026-05-04 08:12:00+00'),
  (14, 'Linear Algebra Done Right', 460000, 18, 4, 'BOOK', TIMESTAMPTZ '2026-05-04 08:13:00+00', TIMESTAMPTZ '2026-05-04 08:13:00+00'),
  (15, 'Introduction to Algorithms (CLRS)', 890000, 14, 4, 'BOOK', TIMESTAMPTZ '2026-05-04 08:14:00+00', TIMESTAMPTZ '2026-05-04 08:14:00+00'),
  (16, 'Database System Concepts', 590000, 22, 4, 'BOOK', TIMESTAMPTZ '2026-05-04 08:15:00+00', TIMESTAMPTZ '2026-05-04 08:15:00+00'),

  -- Novel
  (17, 'Norwegian Wood', 220000, 35, 5, 'BOOK', TIMESTAMPTZ '2026-05-04 08:16:00+00', TIMESTAMPTZ '2026-05-04 08:16:00+00'),
  (18, 'The Alchemist', 189000, 40, 5, 'BOOK', TIMESTAMPTZ '2026-05-04 08:17:00+00', TIMESTAMPTZ '2026-05-04 08:17:00+00'),
  (19, '1984', 210000, 28, 5, 'BOOK', TIMESTAMPTZ '2026-05-04 08:18:00+00', TIMESTAMPTZ '2026-05-04 08:18:00+00'),
  (20, 'The Little Prince', 175000, 50, 5, 'BOOK', TIMESTAMPTZ '2026-05-04 08:19:00+00', TIMESTAMPTZ '2026-05-04 08:19:00+00'),

  -- Laptop
  (21, 'MacBook Air M3 13-inch', 28990000, 12, 6, 'ELECTRONICS', TIMESTAMPTZ '2026-05-04 08:20:00+00', TIMESTAMPTZ '2026-05-04 08:20:00+00'),
  (22, 'Dell XPS 13 (2024)', 32990000, 8, 6, 'ELECTRONICS', TIMESTAMPTZ '2026-05-04 08:21:00+00', TIMESTAMPTZ '2026-05-04 08:21:00+00'),
  (23, 'Lenovo ThinkPad X1 Carbon Gen 12', 39990000, 6, 6, 'ELECTRONICS', TIMESTAMPTZ '2026-05-04 08:22:00+00', TIMESTAMPTZ '2026-05-04 08:22:00+00'),
  (24, 'ASUS VivoBook 15', 15990000, 18, 6, 'ELECTRONICS', TIMESTAMPTZ '2026-05-04 08:23:00+00', TIMESTAMPTZ '2026-05-04 08:23:00+00'),

  -- Mobile
  (25, 'iPhone 15', 22990000, 18, 7, 'ELECTRONICS', TIMESTAMPTZ '2026-05-04 08:24:00+00', TIMESTAMPTZ '2026-05-04 08:24:00+00'),
  (26, 'Samsung Galaxy S24', 20990000, 20, 7, 'ELECTRONICS', TIMESTAMPTZ '2026-05-04 08:25:00+00', TIMESTAMPTZ '2026-05-04 08:25:00+00'),
  (27, 'Xiaomi Redmi Note 13 Pro', 7990000, 32, 7, 'ELECTRONICS', TIMESTAMPTZ '2026-05-04 08:26:00+00', TIMESTAMPTZ '2026-05-04 08:26:00+00'),
  (28, 'Google Pixel 8', 17990000, 10, 7, 'ELECTRONICS', TIMESTAMPTZ '2026-05-04 08:27:00+00', TIMESTAMPTZ '2026-05-04 08:27:00+00'),

  -- Home Appliance
  (29, 'Philips Air Fryer 4.1L', 2190000, 26, 8, 'ELECTRONICS', TIMESTAMPTZ '2026-05-04 08:28:00+00', TIMESTAMPTZ '2026-05-04 08:28:00+00'),
  (30, 'Xiaomi Robot Vacuum S10+', 8990000, 9, 8, 'ELECTRONICS', TIMESTAMPTZ '2026-05-04 08:29:00+00', TIMESTAMPTZ '2026-05-04 08:29:00+00'),
  (31, 'Panasonic Microwave 23L', 2590000, 14, 8, 'ELECTRONICS', TIMESTAMPTZ '2026-05-04 08:30:00+00', TIMESTAMPTZ '2026-05-04 08:30:00+00'),
  (32, 'LG Front Load Washer 9kg', 12990000, 7, 8, 'ELECTRONICS', TIMESTAMPTZ '2026-05-04 08:31:00+00', TIMESTAMPTZ '2026-05-04 08:31:00+00'),

  -- Men Clothing
  (33, 'Men''s Polo Shirt', 299000, 75, 9, 'FASHION', TIMESTAMPTZ '2026-05-04 08:32:00+00', TIMESTAMPTZ '2026-05-04 08:32:00+00'),
  (34, 'Men''s Slim Jeans', 499000, 55, 9, 'FASHION', TIMESTAMPTZ '2026-05-04 08:33:00+00', TIMESTAMPTZ '2026-05-04 08:33:00+00'),
  (35, 'Men''s Formal Shirt', 399000, 50, 9, 'FASHION', TIMESTAMPTZ '2026-05-04 08:34:00+00', TIMESTAMPTZ '2026-05-04 08:34:00+00'),
  (36, 'Men''s Bomber Jacket', 799000, 25, 9, 'FASHION', TIMESTAMPTZ '2026-05-04 08:35:00+00', TIMESTAMPTZ '2026-05-04 08:35:00+00'),

  -- Shoes
  (37, 'Running Shoes Air Zoom', 1299000, 24, 10, 'FASHION', TIMESTAMPTZ '2026-05-04 08:36:00+00', TIMESTAMPTZ '2026-05-04 08:36:00+00'),
  (38, 'Sneakers Court Classic', 1099000, 30, 10, 'FASHION', TIMESTAMPTZ '2026-05-04 08:37:00+00', TIMESTAMPTZ '2026-05-04 08:37:00+00'),
  (39, 'Leather Loafers', 1199000, 20, 10, 'FASHION', TIMESTAMPTZ '2026-05-04 08:38:00+00', TIMESTAMPTZ '2026-05-04 08:38:00+00'),
  (40, 'Sandals Comfort', 399000, 40, 10, 'FASHION', TIMESTAMPTZ '2026-05-04 08:39:00+00', TIMESTAMPTZ '2026-05-04 08:39:00+00');

-- Subtype rows (one per product)
INSERT INTO app_book (product_id, author, publisher, isbn, language, publication_date) VALUES
  (1, 'Andrew Hunt & David Thomas', 'Addison-Wesley', '9780201616224', 'English', NULL),
  (2, 'Robert C. Martin', 'Prentice Hall', '9780132350884', 'English', NULL),
  (3, 'Erich Gamma et al.', 'Addison-Wesley', '9780201633610', 'English', NULL),
  (4, 'Francois Chollet', 'Manning', '9781617294433', 'English', NULL),
  (13, 'James Stewart', 'Cengage Learning', '9781285741550', 'English', NULL),
  (14, 'Sheldon Axler', 'Springer', '9783319110790', 'English', NULL),
  (15, 'Thomas H. Cormen et al.', 'MIT Press', '9780262033848', 'English', NULL),
  (16, 'Abraham Silberschatz et al.', 'McGraw-Hill', '9780078022159', 'English', NULL),
  (17, 'Haruki Murakami', 'Vintage', '9780099448822', 'English', NULL),
  (18, 'Paulo Coelho', 'HarperOne', '9780062315007', 'English', NULL),
  (19, 'George Orwell', 'Signet Classic', '9780451524935', 'English', NULL),
  (20, 'Antoine de Saint-Exupery', 'Mariner Books', '9780156012195', 'English', NULL);

INSERT INTO app_electronics (product_id, model_name, brand, warranty, weight, dimensions, color) VALUES
  (5, 'Flip 6', 'JBL', 12, 0.55, '17.8 x 6.8 x 7.2 cm', 'Black'),
  (6, 'Watch SE 2024', 'Apple', 12, 0.04, '40mm', 'Midnight'),
  (7, 'Archer AX55', 'TP-Link', 24, 0.50, '26.1 x 13.5 x 4.1 cm', 'Black'),
  (8, 'PowerCore 10000', 'Anker', 18, 0.18, '9.2 x 6.0 x 2.2 cm', 'Black'),
  (21, 'Air M3 13', 'Apple', 12, 1.24, '30.4 x 21.5 x 1.1 cm', 'Silver'),
  (22, 'XPS 13 2024', 'Dell', 24, 1.20, '29.5 x 19.9 x 1.5 cm', 'Platinum'),
  (23, 'X1 Carbon Gen 12', 'Lenovo', 36, 1.12, '31.3 x 21.7 x 1.5 cm', 'Black'),
  (24, 'VivoBook 15', 'ASUS', 24, 1.70, '35.7 x 23.5 x 2.0 cm', 'Grey'),
  (25, 'iPhone 15', 'Apple', 12, 0.17, '147.6 x 71.6 x 7.8 mm', 'Blue'),
  (26, 'Galaxy S24', 'Samsung', 12, 0.17, '147.0 x 70.6 x 7.6 mm', 'Black'),
  (27, 'Redmi Note 13 Pro', 'Xiaomi', 12, 0.19, '161.1 x 74.9 x 8.0 mm', 'Green'),
  (28, 'Pixel 8', 'Google', 12, 0.19, '150.5 x 70.8 x 8.9 mm', 'Hazel'),
  (29, 'Air Fryer 4.1L', 'Philips', 12, 4.50, '36.0 x 26.0 x 29.5 cm', 'Black'),
  (30, 'Robot Vacuum S10+', 'Xiaomi', 12, 3.80, '35.0 x 35.0 x 9.7 cm', 'White'),
  (31, 'Microwave 23L', 'Panasonic', 12, 12.00, '48.0 x 39.0 x 28.0 cm', 'Silver'),
  (32, 'Front Load Washer 9kg', 'LG', 24, 60.00, '60.0 x 55.0 x 85.0 cm', 'White');

INSERT INTO app_fashion (product_id, brand, size, color, material, season, gender) VALUES
  (9, 'Local Brand', 'L', 'Black', 'Cotton', 'All-season', 'Unisex'),
  (10, 'Local Brand', 'One Size', 'Navy', 'Cotton', 'All-season', 'Unisex'),
  (11, 'Local Brand', 'M', 'Brown', 'Leather', 'All-season', 'Unisex'),
  (12, 'Local Brand', 'One Size', 'Black', 'Polycarbonate', 'Summer', 'Unisex'),
  (33, 'Local Brand', 'M', 'Navy', 'Cotton', 'All-season', 'Men'),
  (34, 'Local Brand', '32', 'Blue', 'Denim', 'All-season', 'Men'),
  (35, 'Local Brand', 'L', 'White', 'Cotton', 'All-season', 'Men'),
  (36, 'Local Brand', 'L', 'Black', 'Polyester', 'Winter', 'Men'),
  (37, 'Local Brand', '42', 'White', 'Mesh', 'All-season', 'Unisex'),
  (38, 'Local Brand', '41', 'White', 'Leather', 'All-season', 'Unisex'),
  (39, 'Local Brand', '41', 'Brown', 'Leather', 'All-season', 'Men'),
  (40, 'Local Brand', '40', 'Black', 'EVA', 'Summer', 'Unisex');

SELECT setval(pg_get_serial_sequence('app_product', 'id'), (SELECT MAX(id) FROM app_product));