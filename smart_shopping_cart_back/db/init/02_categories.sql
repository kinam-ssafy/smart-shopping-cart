-- 카테고리 데이터
-- 대분류 카테고리 (parent_categories)
INSERT INTO parent_categories (parent_category_id, name) VALUES
('pc-fruits', '과일'),
('pc-vegetables', '채소'),
('pc-dairy', '유제품'),
('pc-meat', '육류'),
('pc-seafood', '수산물'),
('pc-beverages', '음료'),
('pc-snacks', '과자/스낵'),
('pc-frozen', '냉동식품'),
('pc-bakery', '베이커리'),
('pc-household', '생활용품')
ON CONFLICT DO NOTHING;

-- 소분류 카테고리
INSERT INTO categories (category_id, name, parent_category_id) VALUES
-- 과일
('cat-fresh-fruits', '신선과일', 'pc-fruits'),
('cat-tropical-fruits', '열대과일', 'pc-fruits'),
('cat-dried-fruits', '건과일', 'pc-fruits'),
-- 채소
('cat-leafy', '엽채류', 'pc-vegetables'),
('cat-root', '근채류', 'pc-vegetables'),
('cat-mushroom', '버섯류', 'pc-vegetables'),
-- 유제품
('cat-milk', '우유', 'pc-dairy'),
('cat-cheese', '치즈', 'pc-dairy'),
('cat-yogurt', '요거트', 'pc-dairy'),
-- 육류
('cat-beef', '소고기', 'pc-meat'),
('cat-pork', '돼지고기', 'pc-meat'),
('cat-chicken', '닭고기', 'pc-meat'),
-- 수산물
('cat-fish', '생선', 'pc-seafood'),
('cat-shellfish', '조개류', 'pc-seafood'),
-- 음료
('cat-water', '생수/탄산수', 'pc-beverages'),
('cat-juice', '주스', 'pc-beverages'),
('cat-coffee', '커피/차', 'pc-beverages'),
('cat-beverages', '기타음료', 'pc-beverages'),
-- 과자
('cat-chips', '스낵/칩', 'pc-snacks'),
('cat-candy', '사탕/젤리', 'pc-snacks'),
('cat-chocolate', '초콜릿', 'pc-snacks'),
-- 냉동
('cat-frozen-meal', '냉동식품', 'pc-frozen'),
('cat-ice-cream', '아이스크림', 'pc-frozen'),
-- 베이커리
('cat-bread', '빵', 'pc-bakery'),
('cat-cake', '케이크', 'pc-bakery'),
-- 생활용품
('cat-tissue', '화장지/티슈', 'pc-household'),
('cat-detergent', '세제', 'pc-household')
ON CONFLICT DO NOTHING;
