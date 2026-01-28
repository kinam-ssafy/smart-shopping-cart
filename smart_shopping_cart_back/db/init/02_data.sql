INSERT INTO categories (category_id, name)
VALUES
  ('cat-fruit', 'Fruits')
ON CONFLICT DO NOTHING;
INSERT INTO products (
  product_id,
  name,
  category_id,
  price,
  description,
  active,
  bay,
  level,
  position_index,
  stock
) VALUES
('p-apple-red',  'Red Apple',  'cat-fruit', 1.50, 'Fresh red apple',  true, 'A', 1, 0, 50),
('p-apple-green','Green Apple','cat-fruit', 1.40, 'Sour green apple', true, 'A', 1, 1, 40),
('p-banana',     'Banana',     'cat-fruit', 1.20, 'Sweet banana',     true, 'A', 2, 0, 60),
('p-orange',     'Orange',     'cat-fruit', 1.60, 'Juicy orange',     true, 'B', 1, 0, 30),
('p-grape',      'Grape',      'cat-fruit', 2.50, 'Seedless grapes',  true, 'B', 2, 1, 20),
('p-mango',      'Mango',      'cat-fruit', 3.00, 'Tropical mango',   true, 'C', 1, 0, 15)
ON CONFLICT DO NOTHING;
INSERT INTO product_images (
  product_id,
  image_url,
  image_alt_text,
  sort_order
) VALUES
('p-apple-red',   'https://example.com/apple_red.jpg',   'Red Apple',   0),
('p-apple-green', 'https://example.com/apple_green.jpg', 'Green Apple', 0),
('p-banana',      'https://example.com/banana.jpg',      'Banana',      0),
('p-orange',      'https://example.com/orange.jpg',      'Orange',      0),
('p-grape',       'https://example.com/grape.jpg',       'Grape',       0),
('p-mango',       'https://example.com/mango.jpg',       'Mango',       0)
ON CONFLICT DO NOTHING;
INSERT INTO reviews (
  product_id,
  rating,
  content,
  image_url,
  image_alt_text
) VALUES
('p-apple-red',   5, 'Very fresh!',     'https://example.com/r1.jpg', 'review'),
('p-apple-red',   4, 'Tasty apple',     'https://example.com/r2.jpg', 'review'),
('p-banana',      5, 'Perfect banana',  'https://example.com/r3.jpg', 'review'),
('p-banana',      5, 'Sweet!',           'https://example.com/r4.jpg', 'review'),
('p-orange',      3, 'Okay-ish',         'https://example.com/r5.jpg', 'review'),
('p-grape',       4, 'Nice grapes',      'https://example.com/r6.jpg', 'review')
ON CONFLICT DO NOTHING;
INSERT INTO carts (
  cart_id,
  status,
  shopping_list
) VALUES (
  '1',
  'active',
  ARRAY['p-apple-red', 'p-banana', 'p-mango']
)
ON CONFLICT DO NOTHING;
