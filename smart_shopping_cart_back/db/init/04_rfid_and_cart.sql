-- 기타 시드 데이터 (카트 초기화)
-- 03_products.sql 실행 후 실행

-- RFID 매핑은 실제 태그 정보 확보 후 추가 예정
-- INSERT INTO product_rfids (rfid_uid, product_id) VALUES
-- ('XX:XX:XX:XX', 1)
-- ON CONFLICT DO NOTHING;

-- 카트 초기 데이터
INSERT INTO carts (cart_id, status, shopping_list) VALUES
(1, 'active', ARRAY[]::TEXT[])
ON CONFLICT DO NOTHING;
