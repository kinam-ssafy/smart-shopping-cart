-- 기타 시드 데이터 (RFID 매핑, 카트 초기화)
-- 03_products.sql 실행 후 실행

-- RFID 매핑 데이터 (실제 RFID 태그)
-- 03_products.sql 기준 product_id:
-- 1=청송 꿀사과, 2=청송 부사 사과, 3=제주 감귤, 9=바나나
-- 27=서울우유, 28=매일 저지방우유, 44=닭가슴살, 68=포카칩

INSERT INTO product_rfids (rfid_uid, product_id) VALUES
('01:5B:F1:05', 1),   -- 청송 꿀사과
('42:8A:24:9E', 2),   -- 청송 부사 사과
('54:FF:F6:05', 3),   -- 제주 감귤
('57:6B:FA:05', 9),   -- 바나나
('6D:DB:4F:06', 27),  -- 서울우유 1L (수정: 31→27)
('89:8D:EF:7A', 28),  -- 매일 저지방우유 (수정: 32→28)
('89:D0:CF:7A', 44),  -- 닭가슴살 (수정: 52→44)
('A3:0A:52:03', 68)   -- 포카칩 (수정: 76→68)
ON CONFLICT DO NOTHING;

-- RFID가 등록된 상품은 has_rfid를 true로 업데이트
UPDATE products SET has_rfid = true WHERE product_id IN (1, 2, 3, 9, 27, 28, 44, 68);

-- 카트 초기 데이터
INSERT INTO carts (cart_id, status, shopping_list) VALUES
(1, 'active', ARRAY[]::TEXT[])
ON CONFLICT DO NOTHING;
