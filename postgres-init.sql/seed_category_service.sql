-- Seed data for product_service_db categories (requested categories)
-- Run on product_service_db

-- Keep categories deterministic so other seeds (products/orders) can refer to fixed ids.
TRUNCATE TABLE app_book RESTART IDENTITY CASCADE;
TRUNCATE TABLE app_electronics RESTART IDENTITY CASCADE;
TRUNCATE TABLE app_fashion RESTART IDENTITY CASCADE;
TRUNCATE TABLE app_product RESTART IDENTITY CASCADE;
TRUNCATE TABLE app_category RESTART IDENTITY CASCADE;

-- Category.product_type must be one of: BOOK | ELECTRONICS | FASHION
-- Parent-child structure:
--   Book -> Textbook, Novel
--   Electronics -> Laptop, Mobile, Home Appliance
--   Fashion -> Men Clothing, Shoes
INSERT INTO app_category (id, name, parent_id, product_type) VALUES
  (1, 'Book', NULL, 'BOOK'),
  (2, 'Electronics', NULL, 'ELECTRONICS'),
  (3, 'Fashion', NULL, 'FASHION'),
  (4, 'Textbook', 1, 'BOOK'),
  (5, 'Novel', 1, 'BOOK'),
  (6, 'Laptop', 2, 'ELECTRONICS'),
  (7, 'Mobile', 2, 'ELECTRONICS'),
  (8, 'Home Appliance', 2, 'ELECTRONICS'),
  (9, 'Men Clothing', 3, 'FASHION'),
  (10, 'Shoes', 3, 'FASHION');

SELECT setval(pg_get_serial_sequence('app_category', 'id'), (SELECT MAX(id) FROM app_category));