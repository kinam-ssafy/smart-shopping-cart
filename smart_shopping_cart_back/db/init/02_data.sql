-- 카테고리 추가
INSERT INTO categories (category_id, name)
VALUES
  ('cat-fruit', 'Fruits')
ON CONFLICT DO NOTHING;

-- 상품 추가 (product_id는 BIGSERIAL이므로 자동 생성)
INSERT INTO products (
  name,
  category_id,
  price,
  description,
  active,
  has_rfid,
  bay,
  level,
  position_index,
  stock
) VALUES
('Red Apple',   'cat-fruit', 1.50, 'Fresh red apple',  true, true,  'A', 1, 0, 50),
('Green Apple', 'cat-fruit', 1.40, 'Sour green apple', true, true,  'A', 1, 1, 40),
('Banana',      'cat-fruit', 1.20, 'Sweet banana',     true, true,  'A', 2, 0, 60),
('Orange',      'cat-fruit', 1.60, 'Juicy orange',     true, false, 'B', 1, 0, 30),
('Grape',       'cat-fruit', 2.50, 'Seedless grapes',  true, false, 'B', 2, 1, 20),
('Mango',       'cat-fruit', 3.00, 'Tropical mango',   true, false, 'C', 1, 0, 15)
ON CONFLICT DO NOTHING;

-- RFID 매핑 (has_rfid=true인 상품만)
-- 실제 RFID UID와 product_id 매핑
INSERT INTO product_rfids (rfid_uid, product_id) VALUES
('01:5B:F1:05', 1),  -- Red Apple
('54:FF:F6:05', 2),  -- Green Apple
('57:6B:FA:05', 3)   -- Banana
ON CONFLICT DO NOTHING;

-- 상품 이미지
INSERT INTO product_images (
  product_id,
  image_url,
  image_alt_text,
  sort_order
) VALUES
(1, 'https://example.com/apple_red.jpg',   'Red Apple',   0),
(2, 'https://example.com/apple_green.jpg', 'Green Apple', 0),
(3, 'https://example.com/banana.jpg',      'Banana',      0),
(4, 'https://example.com/orange.jpg',      'Orange',      0),
(5, 'https://example.com/grape.jpg',       'Grape',       0),
(6, 'https://example.com/mango.jpg',       'Mango',       0)
ON CONFLICT DO NOTHING;

-- 리뷰
INSERT INTO reviews (
  product_id,
  rating,
  content,
  image_url,
  image_alt_text
) VALUES
(1, 5, 'Very fresh!',     'https://example.com/r1.jpg', 'review'),
(1, 4, 'Tasty apple',     'https://example.com/r2.jpg', 'review'),
(3, 5, 'Perfect banana',  'https://example.com/r3.jpg', 'review'),
(3, 5, 'Sweet!',          'https://example.com/r4.jpg', 'review'),
(4, 3, 'Okay-ish',        'https://example.com/r5.jpg', 'review'),
(5, 4, 'Nice grapes',     'https://example.com/r6.jpg', 'review')
ON CONFLICT DO NOTHING;

-- 카트
INSERT INTO carts (
  cart_id,
  status,
  shopping_list
) VALUES (
  1,
  'active',
  ARRAY[]::TEXT[]  -- 빈 장바구니로 시작
)
ON CONFLICT DO NOTHING;
