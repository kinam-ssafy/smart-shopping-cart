-- 기타 시드 데이터 (RFID 매핑, 카트 초기화)
-- 03_products.sql 실행 후 실행

-- RFID 매핑 데이터 (실제 RFID 태그)
INSERT INTO product_rfids (rfid_uid, product_id) VALUES
('01:5B:F1:05', 1),   -- 청송 꿀사과
('42:8A:24:9E', 2),   -- 청송 부사 사과
('54:FF:F6:05', 3),   -- 제주 감귤
('57:6B:FA:05', 9),   -- 바나나
('6D:DB:4F:06', 31),  -- 서울우유 1L
('89:8D:EF:7A', 32),  -- 매일 저지방우유
('89:D0:CF:7A', 52),  -- 닭가슴살
('A3:0A:52:03', 76)   -- 포카칩
ON CONFLICT DO NOTHING;

-- RFID가 등록된 상품은 has_rfid를 true로 업데이트
UPDATE products SET has_rfid = true WHERE product_id IN (1, 2, 3, 9, 31, 32, 52, 76);

-- 카트 초기 데이터
INSERT INTO carts (cart_id, status, shopping_list) VALUES
(1, 'active', ARRAY[]::TEXT[])
ON CONFLICT DO NOTHING;
